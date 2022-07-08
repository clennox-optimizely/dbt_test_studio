def generate_header():
    return "\n".join(["{{", "\tconfig(", "\t\ttags=['unit-test']", "\t)", "}}", "", "", ""])

def generate_test(model_to_test, description, mock_sources, mock_refs, expect_columns):
    source_mocks = [generate_mock_source(*src) for src in mock_sources]
    ref_mocks = [generate_mock_ref(*ref) for ref in mock_refs]
    expect = generate_expect(expect_columns)

    lines = []

    lines.append(f"{{% call dbt_unit_testing.test('{model_to_test}', '{description}') %}}")
    lines.append("")

    for mock in source_mocks + ref_mocks + [expect]:
        for line in mock:
            lines.append("\t" + line)
        lines.append("")
    
    lines.append("{% endcall %}")

    return "\n".join(lines)

def generate_mock_ref(ref_name, columns):
    return [f"{{% call dbt_unit_testing.mock_ref('{ref_name}', {{'input_format': 'csv'}}) %}}",
            ("\t" + ", ".join(columns)),
            "\t",
            "{% endcall %}"]


def generate_mock_source(source_name, columns):
    return [f"{{% call dbt_unit_testing.mock_source('{source_name}', {{'input_format': 'csv'}}) %}}",
            ("\t" + ", ".join(columns)),
            "\t",
            "{% endcall %}"]


def generate_expect(columns):
    return ["{% call dbt_unit_testing.expect({'input_format': 'csv'}) %}",
            ("\t" + ", ".join(columns)),
            "\t",
            "{% endcall %}"]


if __name__ == '__main__':
    test = generate_test(
        "my_test_model",
        [('src_1', ['s1a', 's1b'])],
        [('ref_1', ['r1a', 'r1b']), ('ref_2', ['r2a', 'r2b', 'r2c'])],
        ['expect_1', 'expect_2']
    )

    for line in test:
        print(line)