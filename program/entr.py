from lark import Lark
import sys, os, subprocess


def ent_to_dot(tree, is_super=False):
    # initialise for references
    entity_set_name = ""
    is_weak = False

    # inheritance constraint defaults
    completeness = "partial"
    disjointness = "overlapping"

    # print(tree.pretty())

    for token in tree.children:
        match token.data:
            case "entity_set_name":
                entity_set_name = str(token.children[0])

                if is_super:
                    inheritance_relationships[entity_set_name] = SuperEntitySet(
                        entity_set_name, completeness, disjointness
                    )

            case "identifying_relationship_set_name":
                iden_rel_sets.append(str(token.children[0]))
                is_weak = True

            case "super_entity_set_name":
                inheritance_relationships[
                    str(token.children[0])
                ].sub_entity_set_names.append(entity_set_name)

            case "completeness_constraint":
                completeness = str(token.children[0].data)

            case "disjointness_constraint":
                disjointness = str(token.children[0].data)

            case "attribute_list":
                attribute_list = token.children

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
        name = ""
        typ = "simple"
        key = "none"
        inner_attributes = (level, [])

        if attribute.children != []:

            if attribute.children[0].data in [
                "primary",
                "discriminator",
            ]:
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
        if attribute.name != "":
            italics = ("<I>", "</I>")
        else:
            italics = ("", "")

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
            f"{indentation}{underline[0]}{bold[0]}{italics[0]}{curly[0]}{attribute.name}{brackets}{curly[1]}{italics[1]}{bold[1]}{underline[1]}"
        )

        if attribute.inner_attributes[1] != []:
            for inner_attribute in attribute.inner_attributes[1]:
                attribute_html(inner_attribute, html)

    def attribute_list():
        for attribute in attributes:
            attribute_html(attribute, html)

        return newline.join(html)

    peripheries = '[peripheries="1" margin="0.06"]' if is_weak else ""

    return f"""
    node [shape=plaintext] {entity_set_name} {peripheries}
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
                BGCOLOR="#FFFFFF"
            >
				{attribute_list()}
            </TD></TR>
        </TABLE>
    >];"""


def rel_to_dot(tree):
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

    peripheries = ' peripheries="2"' if weak else ""

    def participating_entity_set_list():
        port = "" if weak else ":port"

        # headclip = ' headclip="false"' if weak else ""

        html = []
        for i in range(len(participating_entity_sets) - 1):
            dir = (
                ' dir="back"'
                if participating_entity_sets[i].cardinality == "one"
                else ' dir="none"'
            )
            color = (
                ' color="black:invis:black"'
                if participating_entity_sets[i].participation == "total"
                else ""
            )

            html.append(
                f'{participating_entity_sets[i].name}:port -> {relationship_set_name} [minlen="2" arrowtail="vee" headclip="true"{dir}{color}];'
            )

        dir = (
            ' dir="front"'
            if participating_entity_sets[i].cardinality == "one"
            else ' dir="none"'
        )

        html.append(
            f'{relationship_set_name} -> {participating_entity_sets[-1].name}{port} [minlen="2" arrowhead="vee" headclip="true"{dir}{color}];'
        )

        return "\n    ".join(html)

    return f"""
    node [shape=diamond] {relationship_set_name} [style="filled" fillcolor="#E9F7FE" fontname="italic" height="0.8"{peripheries}];

    {participating_entity_set_list()}"""


def inheritance_relationship_list():
    dot = []

    for super_entity_set_name, super_entity_set in inheritance_relationships.items():

        match super_entity_set.completeness:
            case "total":
                labels = []

                match super_entity_set.disjointness:
                    case "overlapping":
                        if len(super_entity_set.sub_entity_set_names) == 1:
                            labels.append(f" label=< {'.' * 6}<I>total</I>>")
                        if len(super_entity_set.sub_entity_set_names) == 2:
                            labels.append(f' label=" {" " * 12}{"." * 38}"')
                            labels.append(f" label=<<I>total</I>>")

                    case "disjoint":
                        labels.append(f" label=< {'.' * 6}<I>total</I>>")

            case "partial":
                labels = ["" for _ in range(len(super_entity_set.sub_entity_set_names))]

        match super_entity_set.disjointness:
            case "overlapping":
                for i, sub_entity_set_name in enumerate(
                    super_entity_set.sub_entity_set_names
                ):
                    dot.append(
                        f'    {sub_entity_set_name}:port -> {super_entity_set_name}:port [minlen="2" dir="front" headclip="true" arrowhead="empty" labelfloat="true" {labels[i]}];'
                    )
            case "disjoint":
                point = '    point [shape="point" width="0.002" height="0.002"];'
                connection = f'{{ {", ".join(super_entity_set.sub_entity_set_names)} }} -> point [minlen="1" dir="none" tailclip="false"];'
                arrow = f'point -> {super_entity_set_name}:port [minlen="1" dir="front" headclip="true" arrowhead="empty"{labels[-1]}];'

                dot.append("\n    ".join([point, connection, arrow]))
    return "\n".join(dot)


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


class SuperEntitySet:
    def __init__(self, name, completeness, disjointness):
        self.name = name
        self.completeness = completeness
        self.disjointness = disjointness
        self.sub_entity_set_names = []

    def __repr__(self):
        return f"{self.name} ({self.completeness}, {self.disjointness}) {self.sub_entity_sets}"


# TODO make sure that these are valid, i.e. EXTENDS and SUPER references match up
inheritance_relationships = {}

for child in parse_tree.children:
    match child.data:
        case "entity_set":
            ent_sets.append(ent_to_dot(child))
        case "weak_entity_set":
            ent_sets.append(ent_to_dot(child))
        case "super_entity_set":
            ent_sets.append(ent_to_dot(child, is_super=True))
        case "relationship_set":
            rel_sets.append(rel_to_dot(child))

graph_prologue = """digraph ER {
    layout=dot;
    overlap=false;
    splines="ortho";
    outputorder="edgesfirst";
    rankdir="BT";"""

sets = "\n".join(ent_sets + rel_sets)

graph_epilogue = "}"

filename = input_root.split("/")[-1]

if not os.path.exists("dot"):
    os.makedirs("dot")

with open(f"dot/{filename}.dot", "w") as out:
    out.write(
        graph_prologue
        + "\n"
        + sets
        + "\n\n"
        + inheritance_relationship_list()
        + "\n"
        + graph_epilogue
        + "\n"
    )

if not os.path.exists("png"):
    os.makedirs("png")

subprocess.call(
    ["zsh", "../scripts/mkpng", f"dot/{filename}.dot", f"png/{filename}.png"]
)
