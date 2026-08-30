"""Unit tests for the symbolic Big-O expression algebra."""

from app.shared.ast.complexity.expression import Complexity, Term


def test_constant_renders_as_o_of_one():
    assert Complexity.constant().render() == "O(1)"
    assert Complexity(frozenset()).render() == "O(1)"


def test_linear_and_power_rendering():
    assert Complexity.linear("n").render() == "O(n)"
    assert Complexity.power("n", 2).render() == "O(n²)"
    assert Complexity.power("n", 3).render() == "O(n³)"
    assert Complexity.power("n", 4).render() == "O(n^4)"


def test_add_keeps_dominant_same_variable_term():
    result = Complexity.linear("n").add(Complexity.power("n", 2))
    assert result.render() == "O(n²)"


def test_add_keeps_incomparable_terms():
    result = Complexity.linear("n").add(Complexity.linear("m"))
    assert result.render() == "O(n + m)"
    assert result.term_strings() == ("n", "m")


def test_add_of_equal_source_collapses():
    result = Complexity.linear("n").add(Complexity.linear("n"))
    assert result.render() == "O(n)"


def test_multiply_sums_exponents():
    result = Complexity.linear("n").multiply(Complexity.linear("n"))
    assert result.render() == "O(n²)"


def test_multiply_by_constant_is_identity():
    result = Complexity.linear("n").multiply(Complexity.constant())
    assert result.render() == "O(n)"


def test_times_log():
    assert Complexity.linear("n").times_log().render() == "O(n log n)"
    assert Complexity.constant().times_log().render() == "O(log n)"


def test_log_term_dominates_plain_linear():
    result = Complexity.linear("n").add(Complexity.linear("n").times_log())
    assert result.render() == "O(n log n)"


def test_exponential_dominates_everything():
    result = Complexity.power("n", 3).add(Complexity.exponential())
    assert result.render() == "O(2^n)"
    assert Complexity.exponential().times_log().render() == "O(2^n)"


def test_terms_ordered_biggest_first():
    result = Complexity.linear("m").add(Complexity.power("n", 2))
    assert result.term_strings() == ("n²", "m")


def test_dominance_is_symbol_aware():
    assert Term((("n", 2),)).dominates(Term((("n", 1),)))
    assert not Term((("n", 1),)).dominates(Term((("m", 1),)))
