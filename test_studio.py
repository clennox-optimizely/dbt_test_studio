import tkinter as tk
from tkinter import W, ttk
from tkinter.filedialog import askdirectory

import dbt_reader
import code_generator

def build_project_selector(master):
    f = tk.Frame(master)
    
    entry = tk.Entry(f)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def get_project():
        picked = askdirectory()
        entry.delete(0, tk.END)
        entry.insert(0, picked)

    button = tk.Button(f, text='Browse', command=get_project)
    button.pack(side=tk.RIGHT, fill=tk.X)

    f.get_project_path = entry.get

    return f


def build_model_selector(master):
    f = tk.Frame(master)

    model_list = tk.Listbox(f)
    model_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def set_models(models):
        model_list.delete(0, tk.END)
        model_list.insert(0, *models)
    f.set_models = set_models

    scrollbar = tk.Scrollbar(f)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    model_list.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=model_list.yview)

    f.get_selected_model = lambda: model_list.get('active')

    return f


def load_project():
    global model_infos
    project_path = project_selector.get_project_path()
    model_infos = dbt_reader.parse_dbt_project(project_path)
    model_selector.set_models([info for info in model_infos if info.startswith('model')])

def select_model():
    selected_model = model_selector.get_selected_model()
    if selected_model is not None:
        dependencies = dbt_reader.dependent_columns(selected_model, model_infos)
        populate_test_spec(model_infos[selected_model], dependencies)

def populate_test_spec(model_to_test, dependencies):
    generated_tests.clear()
    for item in test_spec_frame.winfo_children():
        item.destroy()

    column_selectors = []

    for dependent_model in dependencies:
        dframe = tk.Frame(test_spec_frame)
        tk.Label(dframe, text=dependent_model.split('.')[-1]).pack(side=tk.TOP)
        sub_selectors = []
        for col in dependencies[dependent_model]:
            check_var = tk.IntVar(value=1)
            checkbox = tk.Checkbutton(dframe, text=col, variable=check_var)
            checkbox.pack(side=tk.TOP, anchor=tk.W)
            sub_selectors.append((col, check_var))

        column_selectors.append((dependent_model, sub_selectors))
        dframe.pack(side=tk.LEFT, fill=tk.BOTH, padx=8)
        ttk.Separator(test_spec_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y)

    expectation_selectors = []

    dframe = tk.Frame(test_spec_frame)
    tk.Label(dframe, text="Expectation").pack(side=tk.TOP)
    for col in model_to_test.columns:
        check_var = tk.IntVar(value=1)
        checkbox = tk.Checkbutton(dframe, text=col, variable=check_var)
        checkbox.pack(side=tk.TOP, anchor=tk.W)
        expectation_selectors.append((col, check_var))
    dframe.pack(side=tk.LEFT, fill=tk.BOTH, padx=8)

    
    finalize_frame = tk.Frame(test_spec_frame)

    description_text = tk.StringVar(test_spec_frame, "")

    tk.Label(finalize_frame, text="Description: ").pack(side=tk.LEFT, anchor=tk.N)
    tk.Entry(finalize_frame, width=30, textvariable=description_text).pack(side=tk.TOP, anchor=tk.N, pady=4)

    def build_test():
        test = code_generator.generate_test(
            model_to_test.name.split('.')[-1],
            description_text.get(),
            [(source_name.split('.')[-1], [col for (col, v) in source_columns if v.get() == 1]) for (source_name, source_columns) in column_selectors if source_name.startswith('source')],
            [(ref_name.split('.')[-1], [col for (col, v) in ref_columns if v.get() == 1]) for (ref_name, ref_columns) in column_selectors if ref_name.startswith('model')],
            [col for (col, v) in expectation_selectors if v.get() == 1]
        )
        generated_tests.append(test)
        test_list.insert(tk.END, description_text.get())

    def export_tests():
        builder = code_generator.generate_header()
        for i, test in enumerate(generated_tests):
            builder += test
            if i + 1 < len(generated_tests):
                builder += "\n\nUNION ALL\n\n"

        print(builder)
        window.clipboard_clear()
        window.clipboard_append(builder)

    tk.Button(finalize_frame, text='Build', command=build_test).pack(side=tk.TOP, anchor=tk.N, pady=4)
    tk.Button(finalize_frame, text='Export', command=export_tests).pack(side=tk.TOP, anchor=tk.N, pady=4)

    test_list = tk.Listbox(finalize_frame, width=30)
    test_list.pack(side=tk.TOP, anchor=tk.S, pady=4)

    finalize_frame.pack(side=tk.RIGHT)

    notebook.select(1)

window = tk.Tk()
window.title("dbt Unit Test Studio")

notebook = ttk.Notebook(window)
notebook.pack(fill=tk.BOTH)

# First frame - project loading and model selection
model_infos = None

model_select_frame = ttk.Frame(notebook, padding=8)

project_selector = build_project_selector(model_select_frame)
project_selector.pack(side=tk.TOP, fill=tk.BOTH, pady=4)

tk.Button(model_select_frame, text="Load Project", command=load_project).pack(side=tk.TOP, pady=4)

tk.Button(model_select_frame, text="Build Test", command=select_model).pack(side=tk.BOTTOM, pady=4)

model_selector = build_model_selector(model_select_frame)
model_selector.pack(side=tk.BOTTOM, fill=tk.BOTH, pady=4, expand=True)

notebook.add(model_select_frame, text='Model Selection')

# Second frame - test specification, populated later
test_spec_frame = ttk.Frame(notebook, padding=8)
tk.Label(test_spec_frame, text="Complete previous steps first.").pack()

notebook.add(test_spec_frame, text='Test Specification')


generated_tests = []

window.geometry('800x300')
window.mainloop()