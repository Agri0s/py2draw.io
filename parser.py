import ast
from sys import argv
from uuid import uuid4

from xml.etree.ElementTree import Element, SubElement, tostring

from math import ceil

cell_height = 26

letter_px_size = 12
letter_px_factor = 0.55


def format_var_name(name, primary_type, secondary_type):
        return f"{name} : {primary_type}" if not secondary_type else f"{name} : {primary_type}, {secondary_type}"

def format_met_name(name, args, return_type):
        return f"{name}({', '.join(args)}): {return_type}"

class UMLClass:
    def __init__(self, name, bases=None):
        self.name = name
        self.bases = bases if bases else []
        self.variables = []
        self.methods = []
        self.relations = []
        self.class_id = f"Class_{uuid4().hex}"

    def add_variable(self, name, primary_type, secondary_type=None):
        self.variables.append({'name': name, 'primary_type': primary_type, 'secondary_type': secondary_type, 'id': f"{self.class_id}_{uuid4().hex}",
                              'formatted_name': format_var_name(name, primary_type, secondary_type)})

    def add_method(self, name, args, return_type, docstring=None):
        self.methods.append({'name': name, 'args': args, 'return_type': return_type, 'docstring': docstring, 'id': f"{self.class_id}_{uuid4().hex}",
                             'formatted_name': format_met_name(name, args, return_type)})

    def add_relation(self, relation_type, target_class, source_var):
        self.relations.append({'relation_type': relation_type, 'target_class': target_class, 'source_var': source_var, 'id': f"{self.class_id}_{uuid4().hex}"})

    

class UMLVisitor(ast.NodeVisitor):
    def __init__(self, include_doc = False):
        self.classes = []
        self.include_doc = include_doc

    
    # TODO add support for Union types
    def handle_assign(self, stmt, uml_class, relation_type):
        for target in stmt.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                var_type = type(stmt.value).__name__
                secondary_type = None
                if isinstance(stmt.value, ast.Call):
                    secondary_type = stmt.value.func.id if isinstance(stmt.value.func, ast.Name) else None
                    uml_class.add_relation(relation_type, secondary_type, target.attr)
                elif isinstance(stmt.value, ast.Constant):
                    secondary_type = type(stmt.value.value).__name__
                elif isinstance(stmt.value, ast.Subscript):
                    if isinstance(stmt.value.value, ast.Name) and stmt.value.value.id == 'Tuple':
                        secondary_type = f"Tuple[{', '.join([elt.id for elt in stmt.value.slice.elts])}]"
                    else:
                        secondary_type = stmt.value.value.id
                
                elif (isinstance(stmt.value, ast.Name)) and stmt.value.id == "parent":
                    # Extract the parent type dynamically
                    pass

                else:
                    pass 

                already_exist = False

                for v in uml_class.variables:
                    if v["name"] == target.attr:
                        v["primary_type"] = var_type
                        v["secondary_type"] = secondary_type
                        already_exist = True
                        break
                    
                if not already_exist:
                    uml_class.add_variable(target.attr, var_type, secondary_type)
                

    def handle_ann_assign(self, stmt, uml_class, relation_type):
        if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == "self":
            primary_type = stmt.annotation.value.id if isinstance(stmt.annotation.value, ast.Name) else type(stmt.annotation.value).__name__
            secondary_type = stmt.annotation.slice.id if isinstance(stmt.annotation.slice, ast.Name) else type(stmt.annotation.slice).__name__
            uml_class.add_variable(stmt.target.attr, primary_type, secondary_type)
            uml_class.add_relation(relation_type, secondary_type, stmt.target.attr)

    def visit_ClassDef(self, node):
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        uml_class = UMLClass(node.name, bases)
        for body_item in node.body:
            if isinstance(body_item, ast.Assign):
                self.handle_assign(body_item, uml_class, 'aggregation')
            elif isinstance(body_item, ast.AnnAssign):
                self.handle_ann_assign(body_item, uml_class, 'aggregation')
            elif isinstance(body_item, ast.FunctionDef):
                if body_item.name == "__init__":
                    for stmt in body_item.body:
                        if isinstance(stmt, ast.Assign):
                            self.handle_assign(stmt, uml_class, 'composition')
                        elif isinstance(stmt, ast.AnnAssign):
                            self.handle_ann_assign(stmt, uml_class, 'composition')
                else:
                    args = [arg.arg for arg in body_item.args.args if arg.arg != "self"]
                    return_type = 'None'  # Default return type
                    if body_item.returns:
                        if isinstance(body_item.returns, ast.Name):
                            return_type = body_item.returns.id
                        elif isinstance(body_item.returns, ast.Subscript):
                            if isinstance(body_item.returns.value, ast.Name) and body_item.returns.value.id == 'Tuple':
                                return_type = f"Tuple[{', '.join([elt.id for elt in body_item.returns.slice.elts])}]"
                            else:
                                return_type = body_item.returns.value.id
                        elif isinstance(body_item.returns, ast.Constant):
                            return_type = body_item.returns.value
                        else:
                            return_type = type(body_item.returns).__name__
                    docstring = ast.get_docstring(body_item) if self.include_doc else None
                    uml_class.add_method(body_item.name, args, return_type, docstring)
        self.classes.append(uml_class)
        self.generic_visit(node)

def parse_python_file(file_path, include_doc=False):
    with open(file_path, 'r') as file:
        file_content = file.read()
    
    # Parse the file content into an AST
    tree = ast.parse(file_content)
    
    # Create a visitor and visit all nodes in the AST
    visitor = UMLVisitor(include_doc)
    visitor.visit(tree)

    return visitor.classes

def print_uml(classes):
    for uml_class in classes:
        print(f"Class: {uml_class.name}")
        if uml_class.bases:
            print(f"  Inherits from: {', '.join(uml_class.bases)}")
        print("  Variables:")
        for var in uml_class.variables:
            secondary_type = f", {var['secondary_type']}" if var['secondary_type'] else ""
            print(f"    {var['name']}: {var['primary_type']}{secondary_type}")
        print("  Methods:")
        for method in uml_class.methods:
            docstring = f" - {method['docstring']}" if method['docstring'] else ""
            print(f"    {method['name']}({', '.join(method['args'])}): {method['return_type']}{docstring}")
        print("  Relations:")
        for relation in uml_class.relations:
            print(f"    {relation['relation_type']} with {relation['target_class']} (source variable: {relation['source_var']})")

def generate_drawio_xml(classes):
    mxfile = Element('mxfile', {
        'host': 'Electron',
        'modified': '2024-07-29T16:06:34.368Z',
        'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) draw.io/24.6.4 Chrome/124.0.6367.207 Electron/30.0.6 Safari/537.36',
        'etag': 'U2siYsB3k-YUB959YpKu',
        'version': '24.6.4',
        'type': 'device'
    })

    diagram = SubElement(mxfile, 'diagram', {'name': 'Page-1', 'id': 'page-1'})
    mxGraphModel = SubElement(diagram, 'mxGraphModel', {
        'dx': '1194', 'dy': '814', 'grid': '0', 'gridSize': '10', 'guides': '0',
        'tooltips': '1', 'connect': '1', 'arrows': '1', 'fold': '1', 'page': '1',
        'pageScale': '1', 'pageWidth': '827', 'pageHeight': '1169', 'math': '0', 'shadow': '0'
    })

    root = SubElement(mxGraphModel, 'root')
    SubElement(root, 'mxCell', {'id': '0'})
    SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})

    x_position = 20
    y_position = 20
    dx = 40  # Spacing between elements

    # 
    for class_ in classes:
        total_height = cell_height + cell_height * len(class_.variables) + 8 + cell_height * len(class_.methods)  # Total height calculation

        # Extract lengths
        name_length = len(class_.name)
        variables_max_length = 0
        methods_max_length = 0

        if class_.variables:
            variables_max_length = max(len(var["formatted_name"]) for var in class_.variables)
        if class_.methods:
            methods_max_length = max(len(meth["formatted_name"]) for meth in class_.methods)

        # Find the maximum length
        max_width = ceil(max(name_length, variables_max_length, methods_max_length) * letter_px_size * letter_px_factor) # upper integer

        if max_width < 160:
            max_width = 160

        # Add class
        class_cell = SubElement(root, 'mxCell', {
        'id': class_.class_id,
        'value': class_.name,
        'style': 'swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;whiteSpace=wrap;html=1;',
        'vertex': '1',
        'parent': '1'
        })
        SubElement(class_cell, 'mxGeometry', {
            'x': str(x_position), 'y': str(y_position), 'width': str(max_width), 'height': str(total_height),
            'as': 'geometry'
        })

        current_y_position = cell_height

        # Add variables
        for var in class_.variables:
            variable_cell = SubElement(root, 'mxCell', {
                'id': var["id"],
                'value': format_var_name(var["name"], var["primary_type"], var["secondary_type"]),
                'style': 'text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;whiteSpace=wrap;html=1;',
                'vertex': '1',
                'parent': class_.class_id
            })
            SubElement(variable_cell, 'mxGeometry', {'y': str(current_y_position), 'width': str(max_width), 'height': str(cell_height), 'as': 'geometry'})
            current_y_position += cell_height


            #print(var)

        # Add separator line with width 1
        separator_id = f"{class_.class_id}_separator"
        separator = SubElement(root, 'mxCell', {
            'id': separator_id,
            'style': 'line;strokeColor=#000000;strokeWidth=1;',
            'parent': class_.class_id,
            'vertex': '1'
        })
        SubElement(separator, 'mxGeometry', {'y': str(current_y_position), 'width': str(max_width), 'height': '8', 'as': 'geometry'})
        current_y_position += 8

        # Add methods
        for met in class_.methods:
            method_cell = SubElement(root, 'mxCell', {
                'id': met["id"],
                'value':  format_met_name(met["name"] , met["args"], met["return_type"]),
                'style': 'text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;whiteSpace=wrap;html=1;',
                'vertex': '1',
                'parent': class_.class_id
            })
            SubElement(method_cell, 'mxGeometry', {'y': str(current_y_position), 'width': str(max_width), 'height': str(cell_height), 'as': 'geometry'})
            current_y_position += cell_height
            #print(met)


        x_position += max_width + dx # Adjust the position for the next class based on the max width

    # add relations
    for class_ in classes:
        for relation in class_.relations:
            if relation['relation_type'] == 'aggregation':
                relation_style = 'edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;'
                source = class_.class_id
            elif relation['relation_type'] == 'composition':
                relation_style = 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;'
                source = ''
                
                for var in class_.variables:
                    if var['name'] == relation['source_var']:
                        source = var['id']
                        break
                    else:
                        continue
            else:
                print(f"Relation type {relation['relation_type']} not supported")
                continue
                    
            target = ''

            for target_class in classes:
                if target_class.name == relation['target_class']:
                    target = target_class.class_id
                    break

            if source and target:
                relation_cell = SubElement(root, 'mxCell', {
                    'id': relation['id'],
                    'value': '',
                    'style': relation_style,
                    'edge': '1',
                    'parent': '1',
                    'source': source,
                    'target': target
                })
                SubElement(relation_cell, 'mxGeometry', {'as': 'geometry'})

            else:
                print(f"Relation {relation['relation_type']} with {relation['target_class']} (source variable: {relation['source_var']}) could not be added")


    return mxfile

def write_xml_file(filename, mxfile):
    # Write XML file with UTF-8 encoding
    with open(filename, 'wb') as file:
        file.write(tostring(mxfile, encoding='utf-8', xml_declaration=True))


def take_last_is_duplicate(classes):
    for class_ in classes:

        pass

if __name__ == "__main__":
    if len(argv) < 2:
        print("Usage: python parse_script.py <python_file> [Doc=True]")
    else:
        file_path = argv[1]
        include_doc = 'Doc=True' in argv
        classes = parse_python_file(file_path, include_doc)

        #take_last_is_duplicate(classes)

        #print_uml(classes)
        
        # Generate XML
        mxfile = generate_drawio_xml(classes)
        write_xml_file('output.drawio', mxfile)
