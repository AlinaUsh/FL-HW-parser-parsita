from parsita import *
import sys

'''
mod        -> mod_only def_types | def_types
def_types  -> type def_types | prog
prog       -> prog_line | prog_line prog
prog_line  -> rel .
rel        -> atom :- disj | atom
disj       -> conj ; disj | conj
conj       -> expr , conj | expr
expr       -> atom | ( disj )
atom       -> ID | ID tail
tail       -> atom | inner_atom | inner_atom tail | VAR | VAR tail | list_ | list_ tail
inner_atom -> ( atom ) | ( inner_atom )

type       -> TYPE ID repsep_t DOT
repsep_t   -> rep1sep(typeexpr, TYPE_DIV)
typeexpr   -> ( repsep_t ) | VAR | atom

H_T_list   ->  [ list_seq H_T_DIV VAR ]
list_seq   -> rep1sep(list_elem , LIST_DIV)
list_elem  -> list_ | atom | VAR
list_      -> [ ] | H_T_list | [ list_seq ]  


Keys:
--atom — парсер одинокого атома 
--typeexpr — парсер одинокого типа (без ключевого слова type, имени и точки в конце)
--type — парсер определения типа (с ключевым словом type и точкой в конце)
--module — парсер определения модуля (с ключевым словом module и точкой в конце)
--relation — парсер для определения отношения (со штопором и точкой в конце)
--list — парсер только для списка  
--prog или без ключа — для программы целиком (учитывая опциональность каждой из компонент)
'''


def format_list(list, elem='nil') -> str:
    if (len(list) == 1):
        return ' ( cons ' + list[0] + ' ' + elem + ' ) '
    return ' ( cons ' + list[0] + ' ' + format_list(list[1:], elem) + ' ) '

def format_type_seq(seq) -> str:
    if (len(seq) == 1):
        return seq[0]
    else:
        return '->  ( ' + ' '.join(seq) + ' ) '


class Parser(TextParsers, whitespace=r'[ \t\n\r]*'):
    LIT = reg(r'[a-zA-Z_][a-zA-Z_0-9]*')
    VAR = reg(r'[A-Z][a-zA-Z_0-9]*')

    OPERATOR = reg(r'\:\-')
    CONJ = reg(r'\,')
    DOT = reg(r'\.')
    DISJ = reg(r'\;')
    OPENBR = reg(r'\(')
    CLOSEBR = reg(r'\)')
    TYPE_DIV = lit('->')

    H_T_DIV = lit('|')
    LIST_DIV = lit(',')
    L_BEGIN = lit('[')
    L_END = lit(']')

    MODULE = reg(r'module')
    TYPE = reg(r'type')

    ID = pred(reg(r'[a-z_][a-zA-Z_0-9]*'),
              lambda x: x != 'type' and x != 'module',
              'identifier') > (lambda x: x)

    inner_atom = ((OPENBR & inner_atom & CLOSEBR) > (lambda x: x[1])) \
                 | ((OPENBR & VAR & CLOSEBR) > (lambda x: 'VAR ' + x[1])) \
                 | ((OPENBR & atom & CLOSEBR) > (lambda x:  x[1]))


    tail       = ((inner_atom & tail) > (lambda x: ' ( ' + x[0] + ' ' + x[1] + ' ) ')) \
                 | (inner_atom > (lambda x: ' ( ' + x + ' ) ')) \
                 | ((VAR & tail) > (lambda x: ' ( ( VAR ' + x[0] + ' ) ' + x[1] + ' ) ')) \
                 | (VAR > (lambda x: ' ( VAR ' + x + ' ) ')) \
                 | (atom > (lambda x: ' ( ' + x + ' ) ')) \
                 | ((list_ & tail) > (lambda x: ' ( ' + x[0] + ' ' + x[1] + ' ) ')) \
                 | (list_ > (lambda x: ' ( ' + x + ' ) '))

    atom       = ((ID & tail) > (lambda x: ' ( ( ID ' + x[0] + ' ) ' + x[1] + ' ) ')) \
                 | (ID > (lambda x: ' ( ID ' + x + ' ) '))

    expr       = ((OPENBR & disj & CLOSEBR) > (lambda x: ' ( ' + x[1] + ' ) ')) \
                 | (atom > (lambda x: ' ( ' + x + ' ) '))

    conj       = ((expr & CONJ & conj) > (lambda x: ' ,  ( ' + x[0] + ' ) ( ' + x[2] + ' ) ')) \
                 | (expr > (lambda x: ' ( ' + x + ' ) '))

    disj       = ((conj & DISJ & disj) > (lambda x: ' ; ( ' + x[0] + ' ) ( ' + x[2] + ' ) ')) \
                 | (conj > (lambda x: ' ( ' + x + ' ) '))

    rel        = ((atom & OPERATOR & disj & DOT) > (lambda x: ' :- ' + x[0] + x[2] + '.')) \
                 | ((atom & DOT) > (lambda x: x[0] + '.'))

    prog       = ((rel & prog) > (lambda x: '\n'.join(x)))\
                 | (rel > (lambda x: x))

    typeexpr   = ((OPENBR & repsep_t & CLOSEBR) > (lambda x: x[1])) \
                 | (VAR > (lambda x: 'VAR ' + x)) \
                 | (atom > (lambda x: x))

    repsep_t   = rep1sep(typeexpr, TYPE_DIV) \
                 > (lambda x: format_type_seq(x))

    type       = (TYPE & ID & repsep_t & DOT)\
                 > (lambda x: 'type ' + ' ( ' + x[1] + ' ) ' + x[2] + '.')

    def_types  = ((type & def_types) > (lambda x: '\n'.join(x))) \
                 | (prog > (lambda x: x))

    mod_only = (MODULE & ID & DOT) > (lambda x: 'module ' + x[1] + '.\n')

    mod        = ((mod_only & def_types) > (lambda x: ''.join(x))) \
                | (def_types > (lambda x: x))


    H_T_list   =  ((L_BEGIN & list_seq & H_T_DIV & VAR & L_END) \
                  > (lambda x: format_list(x[1], x[3])))

    list_seq   = (rep1sep(list_elem , LIST_DIV)
                  > (lambda x: x))

    list_elem  = list_ | VAR | atom

    list_      = ((L_BEGIN & L_END) > (lambda x: ' nil ')) \
                 | (H_T_list > (lambda x: x)) \
                 | ((L_BEGIN & list_seq & L_END) > (lambda x: format_list(x[1])))


open_file_error_str = "Failed to open {0}"
input_file_error = 'No input file'


if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print(input_file_error)
        sys.exit(0)

    if (len(sys.argv) == 2):
        try:
            input_file_name = sys.argv[1]
            input = open(input_file_name)
        except Exception:
            print(open_file_error_str.format(input_file_name))
            sys.exit(0)
        output_file_name = input_file_name + ".out"
        output_file = open(output_file_name, "w")
        res = Parser.mod.parse(input.read())
        if (type(res) == Failure):
            print(res.message)
        else:
            output_file.write(res.value)
        input.close()
        output_file.close()
        sys.exit(0)


    try:
        input_file_name = sys.argv[2]
        input = open(input_file_name)
    except Exception:
        print(open_file_error_str.format(input_file_name))
        sys.exit(0)
    output_file_name = input_file_name + ".out"
    output_file = open(output_file_name, "w")

    key = sys.argv[1]
    if (key == '--prog'):
        # output_file.write(Parser.mod.parse(input.read()).value)
        res = Parser.mod.parse(input.read())
    elif (key == '--module'):
        # output_file.write(Parser.mod_only.parse(input.read()).value)
        res = Parser.mod_only.parse(input.read())
    elif (key == '--atom'):
        # output_file.write(Parser.atom.parse(input.read()).value)
        res = Parser.atom.parse(input.read())
    elif (key == '--typeexpr'):
        # output_file.write(Parser.repsep_t.parse(input.read()).value)
        res = Parser.repsep_t.parse(input.read())
    elif (key == '--type'):
        # output_file.write(Parser.type.parse(input.read()).value)
        res = Parser.type.parse(input.read())
    elif (key == '--relation'):
        # output_file.write(Parser.rel.parse(input.read()).value)
        res = Parser.rel.parse(input.read())
    elif (key == '--list'):
        # output_file.write(Parser.list_.parse(input.read()).value)
        res = Parser.list_.parse(input.read())
    else:
        # output_file.write(Parser.mod.parse(input.read()).value)
        res = Parser.mod.parse(input.read())

    if (type(res) == Failure):
        print(res.message)
    else:
        output_file.write(res.value)

    input.close()
    output_file.close()
