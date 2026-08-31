import pickle
from engine.btree import BTree

# Load the database file
with open('backend/data/database.pkl', 'rb') as f:
    data = pickle.load(f)

# You will see the new 'indexes' dictionary containing BTree objects
print("Indexes Dictionary:")
print(data['indexes'])

# For example, to check the BTree for the 'users' table 'id' column:
btree_index = data['indexes']['users']['id']
print(f"\nType of Index: {type(btree_index)}")
