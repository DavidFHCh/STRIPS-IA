
#Practica strips
#Hernandez Chiapa David Felipe
# ------ Dominio -----
import itertools
from collections import deque

class Dominio:
    """ Clase para definir el dominio, o espacio de estados en el cual se plantearán problemas de planeación. """
    def __init__(self, nombre, tipos, predicados, acciones):
        """
        Inicializa un dominio
        :param nombre:
        :param tipos:
        :param predicados:
        :param acciones:
        """
        self.nombre = nombre
        self.tipos = tipos
        self.predicados = predicados
        self.acciones = acciones

    def __str__(self):
        dic = {'name':          self.nombre,
               'types':         "  \n".join(self.tipos),
               'predicates':    "  \n".join(str(p) for p in self.predicados),
               'actions':       "\n".join(str(a) for a in self.acciones)
               }
        return """(define (domain {name})
          (:requirements :strips :typing)
          (:types
            {types})
          (:predicates
            {predicates})
          )
          {actions})
        """.format(**dic)


class Variable:
    """ Variable tipada. """
    def __init__(self, nombre, tipo, valor=None):
        """
        :param nombre: símbolo nombre de esta variable.  Los nombres de variables inician con ?
        :param tipo: tipo de la variable, debe estar registrado en la descripción del dominio
        :param valor: objeto vinculado a esta variable, si es None la variable está libre
        """
        self. nombre = nombre
        self.tipo = tipo
        self.valor = valor

    def __str__(self):
        if self.valor:
            return self.valor.nombre
        return "{} - {}".format(self.nombre, self.tipo)


class Predicado:
    """ Representa un hecho. """
    def __init__(self, nombre, variables, negativo = False):
        """
        Predicados para representar hechos.
        :param nombre:
        :param variables: lista de variables tipadas
        :param negativo: indica un predicado del tipo "no P", utilizable para especificar efectos o metas.
        """
        self.nombre = nombre
        self.variables = variables
        self.negativo = negativo

    def __str__(self):
        pred = "({0} {1})".format(self.nombre, " ".join(str(v) for v in self.variables))
        if self.negativo:
            return "(not {0})".format(pred)
        return pred


class Acción:
    """ Función de transición con su acción correspondiente. """
    def __init__(self, nombre, parámetros, precondiciones, efectos, vars=None):
        """
        Inicializa definición de la función de transición para esta acción.
        :param nombre: nombre de la acción
        :param parámetros: lista de variables tipadas
        :param precondiciones: lista de predicados con variables libres
        :param efectos: lista de predicados con variables libres
        :param vars: lista de variables libres que pueden tomar su valor de cualquier objeto del domino simpre que
               sus valores satisfagan las restriciones de las precondiciones.
        """
        self.nombre = nombre
        self.parámetros = parámetros
        self.precondiciones = precondiciones
        self.efectos = efectos
        self.vars = vars

    def __str__(self):
        dic = {'name':      self.nombre,
               'params':    " ".join(str(p) for p in self.parámetros),   # Podrían reunirse 1o los de tipos iguales
               'prec':      " ".join(str(p) for p in self.precondiciones),
               'efec':      " ".join(str(p) for p in self.efectos)
               }
        if self.vars:
            dic['vars'] = "\n    :vars {}".format(" ".join(str(v) for v in self.vars))
        else:
            dic['vars'] = ""
        return """(:action {name}
            :parameters   ({params}) {vars}
            :precondition (and {prec})
            :effect       (and {efec})
        )
        """.format(**dic)


# ------ Problema -----

class Objeto:
    """ Valor concreto para variables en el dominio. """
    def __init__(self, nombre, tipo):
        """
        Crea un objeto existente en el dominio para este problema.
        :param nombre: Símbolo del objeto
        :param tipo: tipo del objeto
        """
        self.nombre = nombre
        self.tipo = tipo

    def __str__(self):
        return "{} - {}".format(self.nombre, self.tipo)


class Problema:
    """ Definicion de un problema en un dominio particular. """
    def __init__(self, nombre, dominio, objetos, predicados, predicados_meta):
        """
        Problema de planeación en una instancia del dominio.
        :param nombre: nombre del problema
        :param dominio: referencia al objeto con la descripción genérica del dominio
        :param objetos: lista de objetos existentes en el dominio, con sus tipos
        :param predicados: lista de predicados con sus variables aterrizadas, indicando qué cosas son verdaderas en el
               estado inicial.  Todo aquello que no esté listado es falso.
        :param predicados_meta: lista de predicados con sus variables aterrizadas, indicando aquellas cosas que deben
               ser verdaderas al final.  Para indicar que algo debe ser falso, el predicado debe ser negativo.
        """
        self.nombre = nombre
        self.dominio = dominio # ref a objeto Dominio
        self.objetos = objetos
        self.estado = predicados
        self.meta = predicados_meta

    def __str__(self):
        dic = {'name':          self.nombre,
               'domain_name':   self.dominio.nombre,
               'objects':       "\n".join(str(o) for o in self.objetos),
               'init':          "\n".join(str(p) for p in self.estado),
               'goal':          "\n".join(str(p) for p in self.meta)}
        return """(define (problem {name}
          (:domain {domain_name})
          (:objects
            {objects})
          (:init
            {init})
          (:goal
            (and {goal}))
        )
        """.format(**dic)

    def aplicable_ (self, accion):
        """
        Decide si una accion es aplicable en el estado actual.
        :param accion: la accion que se quiere aplicar
        """
        lvars1 = accion.parámetros
        if accion.vars != None:
            lvars1 += accion.vars
        asigs = self.asignar_valor (lvars1)
        if asigs == []:
            return (False, [])
        for susts in asigs:
            for sust in susts:
                sust[0].valor = sust[1]
            if self.satis_est(accion.precondiciones):
                return (True,susts)
        return (False,[])


    def asignar_valor (self,vars):
        """
        Regresa todas la posibles combinaciones de valores
        asignados posibles
        :param vars : la lista de variables
        """
        asigs = []
        for var in vars:
            asigs_var = []
            for o in self.objetos:
                if var.tipo == o.tipo:
                    asigs_var += [(var,o)]
            if asigs_var == []:
                return []
            asigs += [asigs_var]
        final = []
        for asig in itertools.product(*asigs):
            final += [list(asig)]
        return final

    def satis_est (self,preconds):
        """
        Decide si un estado es satisfacible o no.
        """
        for precond in preconds:
            contenido = False
            for cond in self.estado:
                contenido = (precond.nombre == cond.nombre and
                        precond.negativo == cond.negativo and
                        self.vars_eq (precond.variables,cond.variables))
                if contenido:
                    break
            if not contenido:
                return False
        return True

    def vars_eq (self, vars1, vars2):
        """
        Checa que dos listas de variables sean iguales.
        Los nombres de las variables son ignorados.
        """
        if len (vars1) != len (vars2):
            return False
        for condi in range(0,len (vars1)):
            if (vars1[condi].tipo != vars2[condi].tipo or
                vars1[condi].valor != vars2[condi].valor):
                return False
        return True

    def es_meta (self):
        """
        Checa si el estado actual satisface el campo meta.
        """
        for goal in self.meta:
            sat = False
            for estado in self.estado
                if( goal.nombre == estado.nombre and
                    self.vars_eq(goal.variables,estado.variables) and
                    goal.negativo == estado.negativo);
                    sat = True
                    break
            if not sat:
                return False
        return True

class Estado_Nodo:
    def __init__(self,actual,padre,accion):
        self.actual = actual
        self.padre = padre
        self.accion = accion

class Recorrido:

    def __init__(self,cola,incial,problema):
        raiz = Estado_Nodo(incial.estado,None,None)
        self.cola = [raiz]
        self.problema = problema

    def aplicables (self,problema):
        aplic = []
        for a in problema.dominio.acciones:
            foo = problema.aplicable_(a)
            if foo[0] == False:
                continue
            aplic += [(a,foo)]
        return aplic

    def copiar_lista (self,l):
        fin = []
        for x in l:
            fin += [x]
        return fin

    def novo_problema (self,estado):
        return Problema (self.problema.nombre,
                        self.problema.dominio,
                        self.problema.objetos,
                        estado,
                        self.problema.meta)

    def sec_acciones (self,nestado,acciones):
        if nestado.padre == None:
            return acciones
        acciones += [nestado.acciones]
        return self.sec_acciones (nestado.padre,acciones)

    def sustituir (self,post,asignaciones):
        #magia
        return post

    def vars_eq1 (self, vars1, vars2):
        """
        Checa que dos listas de variables sean iguales.
        Los nombres de las variables son ignorados.
        """
        if len (vars1) != len (vars2):
            return False
        for condi in range(0,len (vars1)):
            if (vars1[condi].tipo != vars2[condi].tipo or
                vars1[condi].valor != vars2[condi].valor):
                return False
        return True

    def recorrer (self):
        while (len (self.cola) != 0):
            nestado = self.cola[0]
            self.cola.pop(0)
            problema = self.novo_problema (nestado.actual)
            if problema.es_meta():
                return self.sec_acciones (nestado,[])
            laccion_aplic = self.aplicables (problema)
            for aplic in laccion_aplic:
                estado = []
                post = copiar_lista(aplic[0].efectos)
                postcond = self.sustituir (post,aplic[1])
                estado += postcond
                for pred in nestado.actual:
                    entra = True
                    for pred1 in postcond:
                        if (pred.nombre == pred1.nombre and
                            self.vars_eq1 (pred.variables,pred1.variables)):
                            #esto cubre todos los casos en que las postcondiciones entren al siguiente estado
                            entra = False
                            break
                    if entra:
                        estado += [pred]
                novo_nestado = Estado_Nodo (estado,nestado,aplic[0])
                self.cola.append(novo_estado)

if __name__ == '__main__':
    print("Crea aquí los objetos del problema y pide a la computadora que lo resuelva")

    # Ejemplo de cómo usar las clases
    #p = Predicado('en-tripulación', [Variable('?m', 'marinero')])
    #np = Predicado('en-tripulación', [Variable('?m', 'marinero')], True)
    #dominio = Dominio('Barquito',
    #                  ['marinero'],
    #                  [p],
    #                  [Acción('desembarcar', [Variable('?m', 'marinero')], [p], [np])])
    #print(dominio)

    #popeye = Objeto('Popeye', 'marinero')
    #pobj = Predicado('en-tripulación', [Variable('?m', 'marinero', popeye)])
    #npobj = Predicado('en-tripulación', [Variable('?m', 'marinero', popeye)], True)
    #problema = Problema('baja-de-barquito', dominio, [popeye], [pobj], [npobj])
    #print(problema)

    #Inicio Primer ejercicio
    #Inicio Dominio
    p1 = Predicado('adjacent', [Variable('?l1', 'location'),Variable('?l2', 'location')])
    p2 = Predicado('attached',[Variable('?p', 'pile'),Variable('?l', 'location')])
    p3 = Predicado('belong',[Variable('?k', 'crane'),Variable('?l', 'location')])

    p4 = Predicado('at',[Variable('?r', 'robot'),Variable('?l', 'location')])
    p5 = Predicado('occupied',[Variable('?l', 'location')])
    p6 = Predicado('loaded',[Variable('?r', 'robot'),Variable('?c', 'container')])
    p7 = Predicado('unloaded',[Variable('?r', 'robot')])

    p8 = Predicado('holding',[Variable('?k', 'crane'),Variable('?c', 'container')])
    p9 = Predicado('empty',[Variable('?k', 'crane')])

    p10 = Predicado('in',[Variable('?c', 'container'),Variable('?p', 'pile')])
    p11 = Predicado('top',[Variable('?c', 'container'),Variable('?p', 'pile')])
    p12 = Predicado('on',[Variable('?k1', 'container'),Variable('?k2', 'container')])

    r = Variable('?r', 'robot')
    frm = Variable('?from', 'location')
    to = Variable('?to', 'location')
    k = Variable('?k', 'crane')
    c = Variable('?c', 'container')
    p = Variable('?p', 'pile')
    l = Variable('?l','location')
    els = Variable('?else', 'container')

    ap1 = Predicado('adjacent', [frm,to])
    ap2 = Predicado('at',[r,frm])
    nap3 = Predicado('occupied',[to], True)
    ap4 = Predicado('at',[r,to])
    nap5 = Predicado('occupied',[frm], True)
    ap6 = Predicado('occupied',[to])
    nap7 = Predicado('at',[r,frm], True)

    ap8 = Predicado('at',[r,l])
    ap9 = Predicado('belong',[k,l])
    ap10 = Predicado('holding',[k,c])
    ap11 = Predicado('unloaded',[r])
    ap12 = Predicado('loaded',[r])
    nap13 = Predicado('loaded',[r],True)
    ap14 = Predicado('empty',[k])
    nap15 = Predicado('holding',[k,c],True)

    ap16 = Predicado('belong',[k,l])
    ap17 = Predicado('at',[r,l])
    ap18 = Predicado('loaded',[r,c])
    ap19 = Predicado('empty',[k])
    ap20 = Predicado('unloaded',[r])
    ap21 = Predicado('holding',[k,c])
    nap22 = Predicado('loaded',[r,c],True)
    nap23 = Predicado('empty',[k],True)

    ap24 = Predicado('belong',[k,l])
    ap25 = Predicado('attached',[p,l])
    ap26 = Predicado('empty',[k])
    ap27 = Predicado('in',[c,p])
    ap28 = Predicado('top',[c,p])
    ap29 = Predicado('on',[c,els])
    ap30 = Predicado('holding',[k,c])
    ap31 = Predicado('top',[els,p])
    nap32 = Predicado('in',[c,p],True)
    nap33 = Predicado('top',[c,p],True)
    nap34 = Predicado('on',[c,els],True)
    nap35 = Predicado('empty',[k],True)
    nap36 = Predicado('top',[els,p],True)
    nap37 = Predicado('holding',[k,c],True)

    move = Acción('move',[r,frm,to],[ap1,ap2,nap3],[ap4,nap5,ap6,nap7])
    load = Acción('load',[k,c,r],[ap8,ap9,ap10,ap11],[ap12,nap13,ap14,nap15],[l])
    unload = Acción('unload',[k,c,r],[ap16,ap17,ap18,ap19],[ap20,ap21,nap22,nap23],[l])
    take = Acción('take',[k,c,p],[ap24,ap25,ap26,ap27,ap28,ap29],[ap30,ap31,nap32,nap33,nap34,nap35],[l,els])
    put = Acción('put',[k,c,p],[ap24,ap25,ap30,ap31],[ap27,ap28,ap29,nap36,nap37,ap14],[els,l])

    dominio = Dominio('dock-worker-robot',
                      ['location', 'pile', 'robot', 'crane','container'],
                      [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12],
                      [move, load, unload, take, put])
    #Fin Dominio

    #Inicio Problema
    r1 = Objeto('r1','robot')
    l1 = Objeto('l1','location')
    l2 = Objeto('l2','location')
    k1 = Objeto('k1','crane')
    k2 = Objeto('k2','crane')
    p1 = Objeto('p1','pile')
    q1 = Objeto('q1','pile')
    p2 = Objeto('p2','pile')
    q2 = Objeto('q2','pile')
    ca = Objeto('ca','container')
    cb = Objeto('cb','container')
    cc = Objeto('cc','container')
    cd = Objeto('cd','container')
    ce = Objeto('ce','container')
    cf = Objeto('cf','container')
    pallet = Objeto('pallet','container')

    op1 = Predicado('adjacent', [Variable('?l1', 'location', l1),Variable('?l2', 'location', l2)])
    op2 = Predicado('adjacent', [Variable('?l1', 'location', l2),Variable('?l2', 'location', l1)])

    op3 = Predicado('attached', [Variable('?p', 'pile', p1),Variable('?l', 'location', l1)])
    op4 = Predicado('attached', [Variable('?p', 'pile', q1),Variable('?l', 'location', l1)])
    op5 = Predicado('attached', [Variable('?p', 'pile', p2),Variable('?l', 'location', l2)])
    op6 = Predicado('attached', [Variable('?p', 'pile', q2),Variable('?l', 'location', l2)])

    op7 = Predicado('belong', [Variable('?k', 'crane', k1),Variable('?l', 'location', l1)])
    op8 = Predicado('belong', [Variable('?k', 'crane', k2),Variable('?l', 'location', l2)])

    op9 = Predicado('in', [Variable('?c', 'container', ca),Variable('?p', 'pile', p1)])
    op10 = Predicado('in', [Variable('?c', 'container', cb),Variable('?p', 'pile', p1)])
    op11 = Predicado('in', [Variable('?c', 'container', cc),Variable('?p', 'pile', p1)])
    op12 = Predicado('in', [Variable('?c', 'container', cd),Variable('?p', 'pile', q1)])
    op13 = Predicado('in', [Variable('?c', 'container', ce),Variable('?p', 'pile', q1)])
    op14 = Predicado('in', [Variable('?c', 'container', cf),Variable('?p', 'pile', q1)])

    op15 = Predicado('on', [Variable('?k1', 'container', ca),Variable('?k2', 'container', pallet)])
    op16 = Predicado('on', [Variable('?k1', 'container', cb),Variable('?k2', 'container', ca)])
    op17 = Predicado('on', [Variable('?k1', 'container', cc),Variable('?k2', 'container', cb)])
    op18 = Predicado('on', [Variable('?k1', 'container', cd),Variable('?k2', 'container', pallet)])
    op19 = Predicado('on', [Variable('?k1', 'container', ce),Variable('?k2', 'container', cd)])
    op20 = Predicado('on', [Variable('?k1', 'container', cf),Variable('?k2', 'container', ce)])

    op21 = Predicado('top', [Variable('?c', 'container', cc),Variable('?p', 'pile', p1)])
    op22 = Predicado('top', [Variable('?c', 'container', cf),Variable('?p', 'pile', q1)])
    op23 = Predicado('top', [Variable('?c', 'container', pallet),Variable('?p', 'pile', p2)])
    op24 = Predicado('top', [Variable('?c', 'container', pallet),Variable('?p', 'pile', q2)])

    op25 = Predicado('at', [Variable('?r', 'robot', r1),Variable('?l', 'location', l1)])

    op26 = Predicado('unloaded',[Variable('?r', 'robot', r1)])

    op27 = Predicado('occupied',[Variable('?l', 'location', l1)])

    op28 = Predicado('empty',[Variable('?k', 'crane', k1)])
    op29 = Predicado('empty',[Variable('?k', 'crane', k2)])

    goal1 = Predicado('in',[Variable('?c', 'container', ca),Variable('?p', 'pile', p2)])
    goal2 = Predicado('in',[Variable('?c', 'container', cb),Variable('?p', 'pile', q2)])
    goal3 = Predicado('in',[Variable('?c', 'container', cc),Variable('?p', 'pile', p2)])
    goal4 = Predicado('in',[Variable('?c', 'container', cd),Variable('?p', 'pile', q2)])
    goal5 = Predicado('in',[Variable('?c', 'container', ce),Variable('?p', 'pile', q2)])
    goal6 = Predicado('in',[Variable('?c', 'container', cf),Variable('?p', 'pile', q2)])

    problema = Problema('dwrpb1',
                        dominio,
                        [r1, l1, l2,k1 ,k2 ,p1 ,q1 ,p2, q2, ca, cb, cc, cd, ce, cf, pallet],
                        [op1,op2,op3,op4,op5,op6,op7,op8,op9,op10,op11,op12,op13,op14,op15,op16,op17,op18,op19,op20,op21,op22,op23,op24,op25,op26,op27,op28,op29],
                        [goal1,goal2,goal3,goal4,goal5,goal6])
    #Fin Problema

    print(dominio)
    print(problema)
    #Fin Primer ejercicio.
