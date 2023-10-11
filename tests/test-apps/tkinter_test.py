import tkinter as tk
from tkinter import ttk


def on_item_select(event):
    selected_item = tree.selection()[0]
    item_text = tree.item(selected_item, 'text')
    text.delete("1.0", tk.END)
    text.insert(tk.END, f"You selected: {item_text}")


root = tk.Tk()
root.title("Tree with Subitems on Left, Editable Text on Right")

# Create a Treeview on the left
tree = ttk.Treeview(root)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add top-level items
tree.insert('', 'end', 'item1', text='Item 1')
tree.insert('', 'end', 'item2', text='Item 2')
tree.insert('', 'end', 'item3', text='Item 3')

# Add subitems under 'Item 1'
tree.insert('item1', 'end', 'subitem1', text='Subitem 1')
tree.insert('item1', 'end', 'subitem2', text='Subitem 2')

# Add subitems under 'Item 2'
tree.insert('item2', 'end', 'subitem3', text='Subitem 3')

tree.bind("<<TreeviewSelect>>", on_item_select)

# Create an Editable Text area on the right
text = tk.Text(root)
text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Start the tkinter event loop
root.mainloop()
