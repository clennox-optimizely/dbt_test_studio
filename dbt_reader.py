from os import path
import json
from typing import List

import networkx


class ModelInfo:
    def __init__(self, name, sql, depends_on, columns) -> None:
        self.name = name
        self.sql = sql
        self.depends_on = depends_on
        self.columns = columns

    def __repr__(self) -> str:
        return self.name

class SourceInfo:
    def __init__(self, name, columns) -> None:
        self.name = name
        self.columns = columns

    def __repr__(self) -> str:
        return self.name


def parse_dbt_project(project_root) -> List[ModelInfo]:
    with open(path.join(project_root, 'target', 'catalog.json')) as infile:
        catalog = json.load(infile)
    graph = networkx.read_gpickle(path.join(project_root, 'target', 'graph.gpickle'))

    model_infos = []

    for node_name in catalog['nodes']:
        if node_name.startswith('model'):
            node = catalog['nodes'][node_name]
            if node_name in graph.nodes:
                gnode = graph.nodes[node_name]
                model_infos.append(ModelInfo(node_name, gnode['raw_sql'], gnode['depends_on']['nodes'], node['columns']))

    for source_name in catalog['sources']:
        source = catalog['sources'][source_name]
        model_infos.append(SourceInfo(source_name, source['columns']))

    return {info.name: info for info in model_infos}


def dependent_columns(model, infos):
    model_info = infos[model]
    model_sql = model_info.sql.upper()
    return {
        infos[d].name: [col for col in infos[d].columns if col.upper() in model_sql]
        for d in model_info.depends_on
    }


if __name__ == '__main__':
    infos = parse_dbt_project(r'C:\Users\CoLen\Documents\money-dbt\Billing')
    dependent_columns = dependent_columns('model._dbt_workshop.int_sub_exp_netsuite_to_turnstile', infos)
    print(dependent_columns)