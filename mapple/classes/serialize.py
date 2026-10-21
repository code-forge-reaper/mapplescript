

# Helper to serialize child nodes or lists of them (for to_dict)
def serialize_node(node):
    if hasattr(node, "to_dict"):
        return node.to_dict()
    return repr(node)


def serialize_list(lst):
    return [serialize_node(item) for item in lst]
