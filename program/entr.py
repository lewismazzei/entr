from lark import Lark
import sys, os, subprocess


def entity_set(tree, weak=False):
    entity_set_name = tree.children[0].children[0]

    if weak:
        iden_rel_sets.append(tree.children[1].children[0])
        attribute_list = tree.children[2].children
    else:
        attribute_list = tree.children[1].children

    attributes = []
    for attribute in attribute_list:
        if len(attribute.children) == 2:
            attribute_name = str(attribute.children[1].children[0])
            constraint = attribute.children[0].data
        else:
            attribute_name = str(attribute.children[0].children[0])
            constraint = "none"

        attributes.append((attribute_name, constraint))

    indent = "\t" * 4
    newline = f"\n{indent}<BR/>\n{indent}"

    return f"""
    node [shape=plaintext] {entity_set_name} {'[peripheries="1" margin="0.06"]' if weak else ''}
    [label=<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" PORT="port">
            <TR><TD BGCOLOR="#C7EAFB" CELLPADDING="4">
                <I>{entity_set_name}</I>
            </TD></TR>
            <TR><TD
                BALIGN="LEFT"
                ALIGN="LEFT"
                WIDTH="80"
                HEIGHT="50"
                CELLPADDING="6"
            >
				{newline.join([f"{'<U>' if attribute[1] == 'primary' else ''}<I>{attribute[0]}</I>{'</U>' if attribute[1] == 'primary' else ''}" for attribute in attributes])}
            </TD></TR>
        </TABLE>
    >];"""


def relationship_set(tree):
    relationship_set_name = tree.children[0].children[0]

    weak = True if relationship_set_name in iden_rel_sets else False

    participating_entity_set_list = tree.children[1].children

    class ParticipatingEntitySet:
        def __init__(self, name, participation, cardinality, role):
            self.name = name
            self.participation = participation
            self.cardinality = cardinality
            self.role = role

    participating_entity_sets = []

    for participating_entity_set in participating_entity_set_list:

        participation = "partial"
        cardinality = "many"
        role = ""

        for child in participating_entity_set.children:
            if child.data == "name":
                name = child.children[0]
                continue
            if child.data == "total":
                participation = child.data
                continue
            if child.data == "one":
                cardinality = child.data
                continue
            if child.data == "role":
                role = child.children[0]

        participating_entity_sets.append(
            ParticipatingEntitySet(name, participation, cardinality, role)
        )

    return f"""
    node [shape=diamond] {relationship_set_name} [style="filled" fillcolor="#E9F7FE" fontname="italic" height="0.8"{' peripheries="2"' if weak else ''}];

    {participating_entity_sets[0].name}{":port" if not weak else ""} -> {relationship_set_name} [minlen="2" headport="c" dir="{'back' if participating_entity_sets[0].cardinality == 'one' else 'none'}"{' color="black:invis:black"' if participating_entity_sets[0].participation == 'total' else ""}{' arrowhead="vee"' if participating_entity_sets[0].cardinality == 'one' else ''}{' color="black:invis:black"' if participating_entity_sets[0].participation == 'total' else ''}{' headclip="false"' if not weak else ''}];
    {relationship_set_name} -> {participating_entity_sets[1].name}{":port" if not weak else ""} [minlen="2" dir="{'front' if participating_entity_sets[1].cardinality == 'one' else 'none'}"{' color="black:invis:black"' if participating_entity_sets[1].participation == 'total' else ""}{' arrowhead="vee"' if participating_entity_sets[1].cardinality == 'one' else ''}];"""


parser = Lark(
    open("grammar.lark").read(),
    start=["model"],
)

input_filepath = sys.argv[1]
input_root, input_extension = os.path.splitext(input_filepath)

if input_extension != ".entr":
    print("FileFormatError: Input File Must Of Type 'entr'")
    exit(1)

markup = open(input_filepath).read()
parse_tree = parser.parse(markup)
# print(parse_tree.pretty())
# exit(0)

ent_sets = []
rel_sets = []
iden_rel_sets = []

for child in parse_tree.children:
    match child.data:
        case "entity_set":
            ent_sets.append(entity_set(child))
        case "weak_entity_set":
            ent_sets.append(entity_set(child, weak=True))
        case "relationship_set":
            rel_sets.append(relationship_set(child))

graph_prologue = """digraph ER {
    layout=dot;
    overlap=false;
    splines="ortho";
    outputorder="edgesfirst";"""

sets = "\n".join(ent_sets + rel_sets)

graph_epilogue = "}"

filename = input_root.split("/")[-1]

with open(f"dot/{filename}.dot", "w") as out:
    out.write(graph_prologue + "\n" + sets + "\n" + graph_epilogue + "\n")

subprocess.call(
    ["zsh", "../scripts/mkpng", f"dot/{filename}.dot", f"png/{filename}.png"]
)
