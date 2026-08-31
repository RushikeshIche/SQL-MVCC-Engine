"""
B-Tree Implementation for Database Indexing
"""
from typing import List, Any, Optional

class BTreeNode:
    def __init__(self, leaf: bool = False):
        self.leaf = leaf
        # keys contains unique indexed values
        self.keys: List[Any] = []
        # values contains lists of record_ids corresponding to the keys
        self.values: List[List[Any]] = []
        self.children: List['BTreeNode'] = []

class BTree:
    """
    A simple B-Tree implementation tailored for database indexing.
    Supports non-unique keys by storing a list of record IDs for each key.
    """
    def __init__(self, t: int = 3):
        """
        t is the minimum degree (defines the range for number of keys).
        Every node except root must contain at least t-1 keys.
        Every node can contain at most 2t-1 keys.
        """
        self.root = BTreeNode(True)
        self.t = t

    def _convert_key(self, key: Any) -> Any:
        """Attempt to convert key to a comparable type (e.g., float) if numeric."""
        if isinstance(key, str) and key.replace('.', '', 1).replace('-', '', 1).isdigit():
            return float(key) if '.' in key else int(key)
        return key

    def search(self, key: Any) -> List[Any]:
        """Search for a key and return its list of record IDs."""
        key = self._convert_key(key)
        return self._search_node(self.root, key)

    def _search_node(self, node: BTreeNode, key: Any) -> List[Any]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        
        if node.leaf:
            return []
        
        return self._search_node(node.children[i], key)

    def insert(self, key: Any, value: Any):
        """Insert a value (record_id) for the given key."""
        if key is None:
            return
        key = self._convert_key(key)
        root = self.root
        
        # Check if key already exists, just append the value
        existing_values = self._search_node(root, key)
        if existing_values is not None and len(existing_values) > 0:
            if value not in existing_values:
                existing_values.append(value)
            return

        # If root is full
        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root)
            self._split_child(temp, 0)
            self._insert_non_full(temp, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _split_child(self, parent: BTreeNode, i: int):
        t = self.t
        y = parent.children[i]
        z = BTreeNode(y.leaf)
        
        parent.children.insert(i + 1, z)
        parent.keys.insert(i, y.keys[t - 1])
        parent.values.insert(i, y.values[t - 1])
        
        z.keys = y.keys[t: (2 * t) - 1]
        z.values = y.values[t: (2 * t) - 1]
        y.keys = y.keys[0: t - 1]
        y.values = y.values[0: t - 1]
        
        if not y.leaf:
            z.children = y.children[t: 2 * t]
            y.children = y.children[0: t]

    def _insert_non_full(self, node: BTreeNode, key: Any, value: Any):
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = [value]
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.t) - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def delete(self, key: Any, value: Any):
        """Delete a specific record_id from the key. If no values left, delete the key."""
        if key is None:
            return
        key = self._convert_key(key)
        # For simplicity in this basic B-Tree, we'll just remove the value from the list.
        values = self._search_node(self.root, key)
        if values and value in values:
            values.remove(value)

    def get_all(self) -> List[Any]:
        """Return all record IDs across all keys."""
        result = []
        self._traverse(self.root, result)
        return result

    def _traverse(self, node: BTreeNode, result: List[Any]):
        for i in range(len(node.keys)):
            if not node.leaf:
                self._traverse(node.children[i], result)
            result.extend(node.values[i])
        if not node.leaf:
            self._traverse(node.children[len(node.keys)], result)
