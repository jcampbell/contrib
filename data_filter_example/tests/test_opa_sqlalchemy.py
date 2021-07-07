from data_filter_example import opa
import pytest
import requests


one_table_assert_cases = [
    ('trivial', {
        "a": {
            "b": "foo"
        }
    }, '''package test

        p {
            data.q[x]
            x.b = input.a.b
        }''', True, "q.b = 'foo'"),
    ('anonymous', {
        "a": {
            "c": "bar"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                    }''', False, None),
    (
        'inline', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[_].b = input.a.b
                    }''', True, "q.b = 'foo'"
    ),
('inline named var', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[i].b = input.a.b
                    }''', True, "q.b = 'foo'"),
    ('assigned', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[_] = x
                        x.b = input.a.b
                    }''', True, "q.b = 'foo'"),
    ('double eq', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[_] = x
                        x.b == input.a.b
                    }''', True, "q.b = 'foo'"),
    ('conjunction', {
        "a": {
            "b": "foo",
            "c": "bar"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.c = input.a.c
                    }''', True, "q.b = 'foo' AND q.c = 'bar'"),
    ('disjunction data', {
        "a": {
            "b": "foo",
            "c": ["bar", "IT"]
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.c = input.a.c[_]
                    }''', True, "q.b = 'foo' AND q.c = 'bar' OR q.b = 'foo' AND q.c = 'IT'"),
    ('disjunction rules', {
        "a": {
            "b": "foo",
            "c": "bar"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                    }
                    p {
                        data.q[x]
                        x.c = input.a.c
                    }''', True, "q.b = 'foo' OR q.c = 'bar'"),
    ('undefined context', {
        "a": {
            "b": "foo",
            "c": "bar"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                    }
                    p {
                        data.r[x]  # data.r is undefined so this rule will not contribute to the result.
                        x.b = input.a.b
                    }
                    ''', True, "q.b = 'foo'"),
    ('neq', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.exclude != true
                    }
                    ''', True, "q.b = 'foo' AND q.exclude != 1"),
    ('lt', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.n < 1
                    }
                    ''', True, "q.b = 'foo' AND q.n < 1"),
    ('lte', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.n <= 1
                    }
                    ''', True, "q.b = 'foo' AND q.n <= 1"),
    ('gt', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.n > 1
                    }
                    ''', True, "q.b = 'foo' AND q.n > 1"),
    ('gte', {
        "a": {
            "b": "foo"
        }
    }, '''package test
                    p {
                        data.q[x]
                        x.b = input.a.b
                        x.n >= 1
                    }
                    ''', True, "q.b = 'foo' AND q.n >= 1"),
    (
        'nested',
        {
            "a": 1
        },
        '''package test
                    p {
                        data.q[x]
                        abs(x.a) > input.a
                    }''',
        True,
        'abs(q.a) > 1',
    ),
    (
        'nested conjunction',
        {
            "a": 1
        },
        '''package test
                    p {
                        data.q[x]
                        x.b = 1
                        abs(x.a) > input.a
                    }''',
        True,
        'q.b = 1 AND abs(q.a) > 1',
    ),
    (
        'nested conjunction inline',
        {
            "a": 1
        },
        '''package test
                    p {
                        data.q[i].b = 1
                        abs(data.q[i].a) > input.a
                    }''',
        True,
        'q.b = 1 AND abs(q.a) > 1',
    ),
    (
        'intermediate vars',
        {},
        '''package test
        p {
            data.q = x
            x[i] = y
            y = z
            z.a = 1
            y.b = 2
        }''',
        True,
        'q.a = 1 AND q.b = 2',
    ),
    ('set based', {}, '''package test
        p {
            p1[x]
        }

        p1[x] {
            data.q[x].a = 1
        }

        p1[y] {
            data.q[y].b = 2
        }''', True, 'q.a = 1 OR q.b = 2'),
    (
        'unsupported built-in function',
        {},
        '''package test
        p {
            count(data.q[_].a) > input
        }''',
        opa.TranslationError("operator not supported: count"),
        None,
    ),
    (
        'non-relation expression',
        {},
        '''package test
        p {
            plus(data.q[_].a, 10, 10)
        }''',
        opa.TranslationError('too many arguments'),
        None,
    ),
    (
        'invalid row identifier',
        {},
        '''package test
        p {
            data.q.foo.bar = 10
        }''',
        opa.TranslationError('row identifier type not supported'),
        None,
    ),
]



multi_table_assert_cases = [
    (
        'simple join',
        {},
        '''package test
        p {
            data.q[x].a = data.r[y].b
        }''',
        True,
        ['q JOIN r ON q.a = r.b'],
    ),
    (
        'three-way join',
        {},
        '''package test
        p {
            data.q[x].a = data.r[y].b
            data.q[x].c = data.s[z].c
        }''',
        True,
        ['q JOIN r ON q.a = r.b AND q.c = s.c JOIN s ON q.a = r.b AND q.c = s.c'],
    ),
    (
        'mixed',
        {},
        '''package test
        p {
            data.q[x].a = 10
        }
        p {
            data.q[y].a = data.r[z].b
        }''',
        True,
        ['q.a = 10', 'q JOIN r ON q.a = r.b'],
    ),
    (
        'self-join',
        {},
        '''package test
        p {
            data.q[_].a = 10
            data.q[_].b = 20
        }''',
        opa.TranslationError('self-joins not supported'),
        [],
    ),
]



@pytest.mark.parametrize(
    'note,input,policy,exp_defined,exp_sql',
    one_table_assert_cases,
)
def test_compile_one_table(note, input, policy, exp_defined, exp_sql):
    crunch('data.test.p = true', input, ['q'], 'q', policy, exp_defined, [exp_sql
           if exp_sql is not None else None])


@pytest.mark.parametrize('note,input,policy,exp_defined,exp_sql', one_table_assert_cases)
def test_compile_one_table_double_eq(note, input, policy, exp_defined, exp_sql):
    crunch('data.test.p == true', input, ['q'], 'q', policy, exp_defined, [exp_sql
           if exp_sql is not None else None])


@pytest.mark.parametrize('note,input,policy,exp_defined,exp_sql', multi_table_assert_cases)
def test_compile_multi_table(note, input, policy, exp_defined, exp_sql):
    crunch(
        'data.test.p = true',
        input,
        ['q', 'r', 's'],
        'q',
        policy,
        exp_defined,
        exp_sql or None,
    )


def crunch(query, input, unknowns, from_table, policy, exp_defined, exp_sql):
    import sqlalchemy as sa
    engine = sa.create_engine("sqlite://")
    engine.execute("CREATE TABLE q (b integer, c text, include boolean, exclude boolean, n integer, a integer)")
    engine.execute("CREATE TABLE r (b integer, c text, include boolean, exclude boolean, n integer, a integer)")
    engine.execute("CREATE TABLE s (b integer, c text, include boolean, exclude boolean, n integer, a integer)")

    engine.execute("INSERT INTO q (b, c, include, exclude, n, a) VALUES (\"foo\", \"cat\", true, false, 1, -1), (\"bar\", \"dog\", false, true, 2, -2), (\"baz\", \"fish\", true, false, 3, -3)")
    engine.execute("INSERT INTO r (b, c, include, exclude, n, a) VALUES (-1, \"cat-r\", false, true, 2, -2), (\"bar-r\", \"dog-r\", true, false, 3, -3), (\"baz-r\", \"fish-r\", false, true, 4, -4)")
    engine.execute("INSERT INTO s (b, c, include, exclude, n, a) VALUES (1, \"cat\", true, false, 3, -3), (\"bar-s\", \"dog-s\", true, true, 4, -4), (\"baz-s\", \"fish-s\", true, true, 5, -5)")
    try:
        result = opa.compile_sa(query, input, unknowns, engine, from_table, compile_func=opa.compile_command_line({
            'test.rego': policy,
        }))
    except opa.TranslationError as e:
        if not isinstance(exp_defined, opa.TranslationError):
            raise
        assert str(exp_defined) in str(e)
    else:
        assert result.defined == exp_defined
        if result.defined:
            if exp_sql is None:
                assert result.sql is None
            else:
                # assert [c.sql() for c in result.sql.clauses] == exp_sql
                # assert [str(clause) for clause in result.sql] == exp_sql
                assert [str(clause.compile(engine, compile_kwargs={"literal_binds": True})) for clause in result.sql] == exp_sql
        else:
            assert result.sql is None
