from lark import Lark
import sys, os, subprocess


def entity_set(tree, weak=False):
    entity_set_name = tree.children[0].children[0]

    if weak:
        iden_rel_sets.append(tree.children[1].children[0])
        attribute_list = tree.children[2].children
    else:
        attribute_list = tree.children[1].children

    class Attribute:
        def __init__(self, name, typ, key, inner_attributes):
            self.name = name
            self.typ = typ
            self.key = key
            self.inner_attributes = inner_attributes

        def __repr__(self):
            return f"{self.name}:{self.typ}:{self.key}:{self.inner_attributes}"

    attributes = []

    def scrape_attribute(attribute, level):
        typ = "simple"
        key = "none"
        inner_attributes = (level, [])

        if attribute.children[0].data in ["primary", "discriminator"]:
            key = attribute.children[0].data

            if attribute.children[1].data in [
                "composite",
                "multivalued",
                "derived",
                "derived_multivalued",
                "composite_multivalued",
            ]:
                typ = attribute.children[1].data
        else:
            if attribute.children[0].data in [
                "composite",
                "multivalued",
                "derived",
                "derived_multivalued",
                "composite_multivalued",
            ]:
                typ = attribute.children[0].data

        if "composite" in typ:
            inner_attrs = attribute.children[2].children

            name = str(attribute.children[-1 + len(inner_attrs)].children[0])

            for inner_attribute in inner_attrs:
                (
                    inner_attribute_name,
                    inner_attribute_typ,
                    inner_attribute_key,
                    inner_inner_attributes,
                ) = scrape_attribute(inner_attribute, level + 1)

                inner_attributes[1].append(
                    Attribute(
                        inner_attribute_name,
                        inner_attribute_typ,
                        inner_attribute_key,
                        inner_inner_attributes,
                    )
                )
        else:
            name = str(attribute.children[-1].children[0])

        return name, typ, key, inner_attributes

    for attribute in attribute_list:
        name, typ, key, inner_attributes = scrape_attribute(attribute, 0)

        attributes.append(Attribute(name, typ, key, inner_attributes))

    indent = "\t" * 4
    newline = f"\n{indent}<BR/>\n{indent}"

    html = []

    def attribute_html(attribute, html):
        if attribute.key == "primary":
            underline = ("<U>", "</U>")
        else:
            underline = ("", "")

        if attribute.key == "discriminator":
            bold = ("<B>", "</B>")
        else:
            bold = ("", "")

        if "multivalued" in attribute.typ:
            curly = ("{ ", " }")
        else:
            curly = ("", "")

        if "derived" in attribute.typ:
            brackets = " ( )"
        else:
            brackets = ""

        indentation = " " * 4 * attribute.inner_attributes[0]

        html.append(
            f"{indentation}{underline[0]}{bold[0]}<I>{curly[0]}{attribute.name}{brackets}{curly[1]}</I>{bold[1]}{underline[1]}"
        )

        if attribute.inner_attributes[1] != []:
            for inner_attribute in attribute.inner_attributes[1]:
                attribute_html(inner_attribute, html)

    def attribute_list():
        for attribute in attributes:
            attribute_html(attribute, html)

        return newline.join(html)

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
				{attribute_list()}
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

if not os.path.exists("dot"):
    os.makedirs("dot")

with open(f"dot/{filename}.dot", "w") as out:
    out.write(graph_prologue + "\n" + sets + "\n" + graph_epilogue + "\n")

if not os.path.exists("png"):
    os.makedirs("png")

subprocess.call(
    ["zsh", "../scripts/mkpng", f"dot/{filename}.dot", f"png/{filename}.png"]
)
