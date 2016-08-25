r"""
`k`-regular Sequences

An introduction and formal definition of `k`-regular sequences can be
found, for example, on the :wikipedia:`k-regular_sequence` or in
[AS2003]_.


.. WARNING::

    As this code is experimental, warnings are thrown when a
    `k`-regular sequence space is created for the first time in a
    session (see :class:`sage.misc.superseded.experimental`).

    TESTS::

        sage: Seq2 = kRegularSequenceSpace(2, ZZ)
        doctest:...: FutureWarning: This class/method/function is
        marked as experimental. It, its functionality or its interface
        might change without a formal deprecation.
        See http://trac.sagemath.org/21202 for details.

::

    sage: import logging
    sage: logging.basicConfig()

Examples
========

Binary sum of digits
--------------------

::

    sage: Seq2 = kRegularSequenceSpace(2, ZZ)
    sage: S = Seq2((Matrix([[1, 0], [0, 1]]), Matrix([[0, -1], [1, 2]])),
    ....:          left=vector([0, 1]), right=vector([1, 0]))
    sage: S
    2-regular sequence 0, 1, 1, 2, 1, 2, 2, 3, 1, 2, ...
    sage: all(S[n] == sum(n.digits(2)) for n in srange(10))
    True

Number of odd entries in Pascal's triangle
------------------------------------------

::

    sage: @cached_function
    ....: def u(n):
    ....:     if n <= 1:
    ....:         return n
    ....:     return 2*u(floor(n/2)) + u(ceil(n/2))
    sage: tuple(u(n) for n in srange(10))
    (0, 1, 3, 5, 9, 11, 15, 19, 27, 29)

    sage: U = Seq2((Matrix([[3, 6], [0, 1]]), Matrix([[0, -6], [1, 5]])),
    ....:          left=vector([0, 1]), right=vector([1, 0]), transpose=True)
    sage: all(U[n] == u(n) for n in srange(30))
    True


Various
=======

.. SEEALSO::

    :mod:`recognizable series <sage.combinat.recognizable_series>`,
    :doc:`sage/rings/cfinite_sequence`,
    :doc:`sage/combinat/binary_recurrence_sequences`.

REFERENCES:

.. [AS2003] Jean-Paul Allouche, Jeffrey Shallit,
   *Automatic Sequences: Theory, Applications, Generalizations*,
   Cambridge University Press, 2003.

AUTHORS:

- Daniel Krenn (2016)

ACKNOWLEDGEMENT:

- Daniel Krenn is supported by the
  Austrian Science Fund (FWF): P 24644-N26.


Classes and Methods
===================
"""
#*****************************************************************************
#       Copyright (C) 2016 Daniel Krenn <dev@danielkrenn.at>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.combinat.recognizable_series import RecognizableSeries
from sage.combinat.recognizable_series import RecognizableSeriesSpace
from sage.misc.cachefunc import cached_function, cached_method
from six import iteritems


def pad_right(T, length, zero=0):
    r"""
    Pad ``T`` to the right by ``zero``s to have
    at least the given ``length``.

    INPUT:

    - ``T`` -- A tuple, list or other iterable.

    - ``length`` -- a nonnegative integer.

    - ``zero`` -- (default: ``0``) the elements to pad with.

    OUTPUT:

    An object of the same type as ``T``.

    EXAMPLES::

        sage: from sage.combinat.k_regular_sequence import pad_right
        sage: pad_right((1,2,3), 10)
        (1, 2, 3, 0, 0, 0, 0, 0, 0, 0)
        sage: pad_right((1,2,3), 2)
        (1, 2, 3)

    TESTS::

        sage: pad_right([1,2,3], 10)
        [1, 2, 3, 0, 0, 0, 0, 0, 0, 0]
    """
    return T + type(T)(zero for _ in xrange(length - len(T)))


def value(D, k):
    r"""
    Return the value of the expansion with digits `D` in base `k`, i.e.

    .. MATH::

        \sum_{0\leq j < \operator{len}D} D[j] k^j.

    INPUT:

    - ``D`` -- a tuple or other iterable.

    - ``k`` -- the base.

    OUTPUT:

    An element in the common parent of the base `k` and of the entries
    of `D`.

    EXAMPLES::

        sage: from sage.combinat.k_regular_sequence import value
        sage: value(42.digits(7), 7)
        42
    """
    return sum(d * k**j for j, d in enumerate(D))


def split_interlace(n, k, p):
    r"""
    Split each digit in the `k`-ary expansion of `n` into `p` parts and
    return the value of the expansion obtained by each of these parts.

    INPUT:

    - ``n`` -- an integer.

    - ``k`` -- an integer specifying the base.

    - ``p`` -- a positive integer specifying in how many parts
      the input ``n`` is split. This has to be a divisor of ``k``.

    OUTPUT:

    A tuple of integers.

    EXAMPLES::

        sage: from sage.combinat.k_regular_sequence import split_interlace
        sage: [(n, split_interlace(n, 4, 2)) for n in srange(20)]
        [(0, (0, 0)), (1, (1, 0)), (2, (0, 1)), (3, (1, 1)),
         (4, (2, 0)), (5, (3, 0)), (6, (2, 1)), (7, (3, 1)),
         (8, (0, 2)), (9, (1, 2)), (10, (0, 3)), (11, (1, 3)),
         (12, (2, 2)), (13, (3, 2)), (14, (2, 3)), (15, (3, 3)),
         (16, (4, 0)), (17, (5, 0)), (18, (4, 1)), (19, (5, 1))]
        sage: [(n, split_interlace(n, 6, 3)) for n in srange(9)]
        [(0, (0, 0, 0)), (1, (1, 0, 0)), (2, (0, 1, 0)),
         (3, (1, 1, 0)), (4, (0, 0, 1)), (5, (1, 0, 1)),
         (6, (2, 0, 0)), (7, (3, 0, 0)), (8, (2, 1, 0))]

    TESTS::

        sage: split_interlace(42, 4, 3)
        Traceback (most recent call last):
        ...
        ValueError: p=3 is not a divisor of k=4.
    """
    if k % p != 0:
        raise ValueError('p={} is not a divisor of k={}.'.format(p, k))
    ki = k // p
    return tuple(value(D, ki)
                 for D in zip(*(d.digits(ki, padto=p)
                                for d in n.digits(k, padto=1))))


class kRegularSequence(RecognizableSeries):

    def __init__(self, parent, mu, left=None, right=None):
        r"""
        A `k`-regular sequence.

        INPUT:

        - ``parent`` -- an instance of :class:`kRegularSequenceSpace`.

        - ``mu`` -- a family of square matrices, all of which have the
          same dimension. The indices of this family are `0,...,k-1`.
          ``mu`` may be a list or tuple of cardinality `k`
          as well. See
          :meth:`~sage.combinat.recognizable_series.RecognizableSeries.mu`
          for more details.

        - ``left`` -- (default: ``None``) a vector.
          When evaluating the sequence, this vector is multiplied
          from the left to the matrix product. If ``None``, then this
          multiplication is skipped.

        - ``right`` -- (default: ``None``) a vector.
          When evaluating the sequence, this vector is multiplied
          from the left to the matrix product. If ``None``, then this
          multiplication is skipped.

        When created via the parent :class:`kRegularSequenceSpace`, then
        the following option is available.

        - ``transpose`` -- (default: ``False``) a boolean. If set, then
            each of the matrices in
            :meth:`mu <sage.combinat.recognizable_series.RecognizableSeries.mu>`
            is transposed. Additionally the vectors
            :meth`left <sage.combinat.recognizable_series.RecognizableSeries.left>`
            and
            :meth:`right <sage.combinat.recognizable_series.RecognizableSeries.right>`
            are switched.
            (This is done by calling :meth:`~sage.combinat.recognizable_series.RecognizableSeries.transposed`.)

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: Seq2((Matrix([[3, 6], [0, 1]]), Matrix([[0, -6], [1, 5]])),
            ....:      vector([0, 1]), vector([1, 0]),
            ....:      transpose=True)
            2-regular sequence 0, 1, 3, 5, 9, 11, 15, 19, 27, 29, ...

        .. SEEALSO::

            :doc:`k-regular sequence <k_regular_sequence>`,
            :class:`kRegularSequenceSpace`.
        """
        super(kRegularSequence, self).__init__(
            parent=parent, mu=mu, left=left, right=right)


    def _repr_(self):
        r"""
        Return a representation string of this `k`-regular sequence.

        OUTPUT:

        A string.

        TESTS::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: s = Seq2((Matrix([[3, 6], [0, 1]]), Matrix([[0, -6], [1, 5]])),
            ....:           vector([0, 1]), vector([1, 0]), transpose=True)
            sage: repr(s)  # indirect doctest
            '2-regular sequence 0, 1, 3, 5, 9, 11, 15, 19, 27, 29, ...'
        """
        from sage.misc.lazy_list import lazy_list_formatter
        return lazy_list_formatter(
            self,
            name='{}-regular sequence'.format(self.parent().k),
            opening_delimiter='', closing_delimiter='',
            preview=10)


    @cached_method
    def __getitem__(self, n, **kwds):
        r"""
        Return the `n`th entry of this sequence.

        INPUT:

        - ``n`` -- a nonnegative integer.

        OUTPUT:

        An element of the universe of the sequence.

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: S = Seq2((Matrix([[1, 0], [0, 1]]), Matrix([[0, -1], [1, 2]])),
            ....:          left=vector([0, 1]), right=vector([1, 0]))
            sage: S[7]
            3

        TESTS::

            sage: S[-1]
            Traceback (most recent call last):
            ...
            OverflowError: can't convert negative value to unsigned char

        ::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: W = Seq2.indices()
            sage: M0 = Matrix([[1, 0], [0, 1]])
            sage: M1 = Matrix([[0, -1], [1, 2]])
            sage: S = Seq2((M0, M1), vector([0, 1]), vector([1, 1]))
            sage: S._mu_of_word_(W(0.digits(2))) == M0
            True
            sage: S._mu_of_word_(W(1.digits(2))) == M1
            True
            sage: S._mu_of_word_(W(3.digits(2))) == M1^2
            True
        """
        return self.coefficient_of_word(self.parent()._n_to_index_(n), **kwds)


    def __iter__(self):
        r"""
        Return an iterator.

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: S = Seq2((Matrix([[1, 0], [0, 1]]), Matrix([[0, -1], [1, 2]])),
            ....:          left=vector([0, 1]), right=vector([1, 0]))
            sage: from itertools import islice
            sage: tuple(islice(S, 10))
             (0, 1, 1, 2, 1, 2, 2, 3, 1, 2)

        TESTS::

            sage: it = iter(S)
            sage: iter(it) is it
            True
            sage: iter(S) is not it
            True
        """
        from itertools import count
        return iter(self[n] for n in count())


    def subsequence(self, a, b, minimize=True):
        r"""
        Return the subsequence with indices `an+b` of this
        `k`-regular sequence.

        INPUT:

        - ``a`` -- a nonnegative integer.

        - ``b`` -- an integer.

          Alternatively, this is allowed to be a dictionary
          `b_j \mapsto c_j`. If so, the result will be the sum
          of all `c_j(an+b_j)`.

        - ``minimize`` -- (default: ``True``) a boolean. If set, then
          :meth:`minimized` is called after the addition.

        OUTPUT:

        A :class:`kRegularSequence`.

        .. NOTE::

            If `b` is negative (i.e., right-shift), then the
            coefficients when accessing negative indices are `0`.

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: C = Seq2((Matrix([[2, 0], [2, 1]]), Matrix([[0, 1], [-2, 3]])),
            ....:          vector([1, 0]), vector([0, 1]))
            sage: C
            2-regular sequence 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ...

            sage: C.subsequence(2, 0)
            2-regular sequence 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, ...

            sage: S = C.subsequence(3, 1)
            sage: S
            2-regular sequence 1, 4, 7, 10, 13, 16, 19, 22, 25, 28, ...
            sage: S.mu[0], S.mu[1], S.left, S.right
            (
            [ 0  1]  [ 6 -2]
            [-2  3], [10 -3], (1, 0), (1, 1)
            )

            sage: C.subsequence(3, 2)
            2-regular sequence 2, 5, 8, 11, 14, 17, 20, 23, 26, 29, ...

        ::

            sage: S = C.subsequence(1, -1)
            sage: S
            2-regular sequence 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, ...
            sage: S.mu[0], S.mu[1], S.left, S.right
            (
            [ 0  1  0]  [ -2   2   0]
            [-2  3  0]  [  0   0   1]
            [-4  4  1], [ 12 -12   5], (1, 0, 0), (0, 0, 1)
            )

        We can build :meth:`backward_differences` manually by passing
        a dictionary for the parameter ``b``::

            sage: C.subsequence(1, {0: 1, -1: -1})
            2-regular sequence 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, ...

        TESTS::

            sage: C.subsequence(0, 4)
            2-regular sequence 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, ...
            sage: C.subsequence(1, 0) is C
            True

        The following test that the range for `c` in the code
        is sufficient::

            sage: C.subsequence(1, -1, minimize=False)
            2-regular sequence 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, ...
            sage: C.subsequence(1, -2, minimize=False)
            2-regular sequence 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, ...
            sage: C.subsequence(2, -1, minimize=False)
            2-regular sequence 0, 1, 3, 5, 7, 9, 11, 13, 15, 17, ...
            sage: C.subsequence(2, -2, minimize=False)
            2-regular sequence 0, 0, 2, 4, 6, 8, 10, 12, 14, 16, ...

            sage: C.subsequence(2, 21, minimize=False)
            2-regular sequence 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, ...
            sage: C.subsequence(2, 20, minimize=False)
            2-regular sequence 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, ...
            sage: C.subsequence(2, 19, minimize=False)
            2-regular sequence 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, ...
            sage: C.subsequence(2, -9, minimize=False)
            2-regular sequence 0, 0, 0, 0, 0, 1, 3, 5, 7, 9, ...

            sage: C.subsequence(3, 21, minimize=False)
            2-regular sequence 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, ...
            sage: C.subsequence(3, 20, minimize=False)
            2-regular sequence 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, ...
            sage: C.subsequence(3, 19, minimize=False)
            2-regular sequence 19, 22, 25, 28, 31, 34, 37, 40, 43, 46, ...
            sage: C.subsequence(3, 18, minimize=False)
            2-regular sequence 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, ...

            sage: C.subsequence(10, 2, minimize=False)
            2-regular sequence 2, 12, 22, 32, 42, 52, 62, 72, 82, 92, ...
            sage: C.subsequence(10, 1, minimize=False)
            2-regular sequence 1, 11, 21, 31, 41, 51, 61, 71, 81, 91, ...
            sage: C.subsequence(10, 0, minimize=False)
            2-regular sequence 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, ...
            sage: C.subsequence(10, -1, minimize=False)
            2-regular sequence 0, 9, 19, 29, 39, 49, 59, 69, 79, 89, ...
            sage: C.subsequence(10, -2, minimize=False)
            2-regular sequence 0, 8, 18, 28, 38, 48, 58, 68, 78, 88, ...

        ::

            sage: C.subsequence(-1, 0)
            Traceback (most recent call last):
            ...
            ValueError: a=-1 is not nonnegative.
        """
        from sage.rings.integer_ring import ZZ
        zero = ZZ(0)
        a = ZZ(a)
        if not isinstance(b, dict):
            b = {ZZ(b): ZZ(1)}

        if a == 0:
            return sum(c_j * self[b_j] * self.parent().one_hadamard()
                       for b_j, c_j in iteritems(b))
        elif a == 1 and len(b) == 1 and zero in b:
            return b[zero] * self
        elif a < 0:
            raise ValueError('a={} is not nonnegative.'.format(a))

        from sage.arith.srange import srange
        from sage.matrix.constructor import Matrix
        from sage.modules.free_module_element import vector
        P = self.parent()
        A = P.alphabet()
        k = P.k
        dim = self.dimension()

        # Below, we use a dynamic approach to find the shifts of the
        # sequences in the kernel. According to [AS2003]_, the static range
        #    [min(b, 0), max(a, a + b))
        # suffices. However, it seems that the smaller set
        #    [min(b, 0), max(a, a + (b-1)//k + 1)) \cup {b}
        # suffices as well.
        kernel = list(b)

        def pad(T, d):
            di = kernel.index(d)
            return (di*dim)*(0,) + T
        def mu_line(r, i, c):
            d, f = (a*r + c).quo_rem(k)
            if d not in kernel:
                kernel.append(d)
            return pad(tuple(self.mu[f].rows()[i]), d)

        lines = dict((r, []) for r in A)
        ci = 0
        while ci < len(kernel):
            c = kernel[ci]
            for r in A:
                for i in srange(dim):
                    lines[r].append(mu_line(r, i, c))
            ci += 1

        ndim = len(kernel) * dim
        result = P.element_class(
            P,
            dict((r, Matrix([pad_right(row, ndim, zero=zero)
                             for row in lines[r]]))
                 for r in A),
            sum(c_j * vector(
                    pad_right(pad(tuple(self.left), b_j), ndim, zero=zero))
                for b_j, c_j in iteritems(b)),
            vector(sum((tuple(self.__getitem__(c, multiply_left=False))
                        if c >= 0 else dim*(zero,)
                        for c in kernel), tuple())))

        if minimize:
            return result.minimized()
        else:
            return result


    def backward_differences(self, **kwds):
        r"""
        Return the sequence of backward differences of this
        `k`-regular sequence.

        INPUT:

        - ``minimize`` -- (default: ``True``) a boolean. If set, then
          :meth:`minimized` is called after the addition.

        OUTPUT:

        A :class:`kRegularSequence`.

        .. NOTE::

            The coefficient to the index `-1` is `0`.

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: C = Seq2((Matrix([[2, 0], [2, 1]]), Matrix([[0, 1], [-2, 3]])),
            ....:          vector([1, 0]), vector([0, 1]))
            sage: C
            2-regular sequence 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ...
            sage: C.backward_differences()
            2-regular sequence 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, ...

        ::

            sage: E = Seq2((Matrix([[0, 1], [0, 1]]), Matrix([[0, 0], [0, 1]])),
            ....:          vector([1, 0]), vector([1, 1]))
            sage: E
            2-regular sequence 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, ...
            sage: E.backward_differences()
            2-regular sequence 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, ...
        """
        return self.subsequence(1, {0: 1, -1: -1}, **kwds)


    def forward_differences(self, **kwds):
        r"""
        Return the sequence of forward differences of this
        `k`-regular sequence.

        INPUT:

        - ``minimize`` -- (default: ``True``) a boolean. If set, then
          :meth:`minimized` is called after the addition.

        OUTPUT:

        A :class:`kRegularSequence`.

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: C = Seq2((Matrix([[2, 0], [2, 1]]), Matrix([[0, 1], [-2, 3]])),
            ....:          vector([1, 0]), vector([0, 1]))
            sage: C
            2-regular sequence 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ...
            sage: C.forward_differences()
            2-regular sequence 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ...

        ::

            sage: E = Seq2((Matrix([[0, 1], [0, 1]]), Matrix([[0, 0], [0, 1]])),
            ....:          vector([1, 0]), vector([1, 1]))
            sage: E
            2-regular sequence 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, ...
            sage: E.forward_differences()
            2-regular sequence -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, ...
        """
        return self.subsequence(1, {1: 1, 0: -1}, **kwds)


    def partial_sums(self, include_n=False, minimize=True):
        r"""
        Return the sequence of partial sums of this
        `k`-regular sequence. That is, the `n`th entry of the result
        is the sum of the first `n` entries in the original sequence.

        INPUT:

        - ``include_n`` -- (default: ``False``) a boolean. If set, then
          the `n`th entry of the result is the sum of the entries up
          to index `n` (included).

        - ``minimize`` -- (default: ``True``) a boolean. If set, then
          :meth:`minimized` is called after the addition.

        OUTPUT:

        A :class:`kRegularSequence`.

        EXAMPLES::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)

            sage: E = Seq2((Matrix([[0, 1], [0, 1]]), Matrix([[0, 0], [0, 1]])),
            ....:          vector([1, 0]), vector([1, 1]))
            sage: E
            2-regular sequence 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, ...
            sage: E.partial_sums()
            2-regular sequence 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, ...
            sage: E.partial_sums(include_n=True)
            2-regular sequence 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, ...

        ::

            sage: C = Seq2((Matrix([[2, 0], [2, 1]]), Matrix([[0, 1], [-2, 3]])),
            ....:          vector([1, 0]), vector([0, 1]))
            sage: C
            2-regular sequence 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ...
            sage: C.partial_sums()
            2-regular sequence 0, 0, 1, 3, 6, 10, 15, 21, 28, 36, ...
            sage: C.partial_sums(include_n=True)
            2-regular sequence 0, 1, 3, 6, 10, 15, 21, 28, 36, 45, ...

        TESTS::

            sage: E.mu[0], E.mu[1], E.left, E.right
            (
            [0 1]  [0 0]
            [0 1], [0 1], (1, 0), (1, 1)
            )
            sage: P = E.partial_sums(minimize=False)
            sage: P.mu[0], P.mu[1], P.left, P.right
            (
            [ 0  1  0  0]  [0 1 0 0]
            [ 0  2  0 -1]  [0 2 0 0]
            [ 0  0  0  1]  [0 0 0 0]
            [ 0  0  0  1], [0 0 0 1], (1, 0, -1, 0), (1, 1, 1, 1)
            )
        """
        from sage.matrix.constructor import Matrix
        from sage.matrix.special import zero_matrix
        from sage.modules.free_module_element import vector

        P = self.parent()
        A = P.alphabet()
        k = P.k
        dim = self.dimension()

        B = dict((r, sum(self.mu[a] for a in A[r:])) for r in A)
        Z = zero_matrix(dim)
        B[k] = Z
        W = B[0].stack(Z)

        result = P.element_class(
            P,
            dict((r, W.augment((-B[r+1]).stack(self.mu[r])))
                 for r in A),
            vector(tuple(self.left) +
                   (dim*(0,) if include_n else tuple(-self.left))),
            vector(2*tuple(self.right)))

        if minimize:
            return result.minimized()
        else:
            return result


def _pickle_kRegularSequenceSpace(k, coefficients, category):
    r"""
    Pickle helper.

    TESTS::

        sage: Seq2 = kRegularSequenceSpace(2, ZZ)
        sage: from sage.combinat.k_regular_sequence import _pickle_kRegularSequenceSpace
        sage: _pickle_kRegularSequenceSpace(
        ....:     Seq2.k, Seq2.coefficients(), Seq2.category())
        Space of 2-regular sequences over Integer Ring
    """
    return kRegularSequenceSpace(k, coefficients, category=category)


class kRegularSequenceSpace(RecognizableSeriesSpace):
    r"""
    The space of `k`-regular Sequences over the given ``coefficients``.

    INPUT:

    - ``k`` -- an integer at least `2` specifying the base.

    - ``coefficients`` -- a (semi-)ring. If not specified (``None``),
      then the integer ring is used.

    - ``category`` -- (default: ``None``) the category of this
      space.

    EXAMPLES::

        sage: kRegularSequenceSpace(2, ZZ)
        Space of 2-regular sequences over Integer Ring
        sage: kRegularSequenceSpace(3, ZZ)
        Space of 3-regular sequences over Integer Ring

    .. SEEALSO::

        :doc:`k-regular sequence <k_regular_sequence>`,
        :class:`kRegularSequence`.
    """

    Element = kRegularSequence


    @classmethod
    def __normalize__(cls, k, coefficients=None, **kwds):
        r"""
        Normalizes the input in order to ensure a unique
        representation.

        For more information see :class:`kRegularSequenceSpace`.

        TESTS::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: Seq2.category()
            Category of modules over Integer Ring

        ::

            sage: Seq2 is kRegularSequenceSpace(2)
            True
        """
        from sage.arith.srange import srange
        from sage.rings.integer_ring import ZZ
        if coefficients is None:
            coefficients = ZZ
        nargs = super(kRegularSequenceSpace, cls).__normalize__(
            coefficients, alphabet=srange(k), **kwds)
        return (k,) + nargs


    def __init__(self, k, *args, **kwds):
        r"""
        See :class:`kRegularSequenceSpace` for details.

        INPUT:

        - ``k`` -- an integer at least `2` specifying the base.

        Other input arguments are passed on to
        :meth:`~sage.combinat.recognizable_series.RecognizableSeriesSpace.__init__`.

        TESTS::

            sage: kRegularSequenceSpace(2, ZZ)
            Space of 2-regular sequences over Integer Ring
            sage: kRegularSequenceSpace(3, ZZ)
            Space of 3-regular sequences over Integer Ring

        ::

            sage: from itertools import islice
            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: TestSuite(Seq2).run(  # long time
            ....:    verbose=True,
            ....:    elements=tuple(islice(Seq2.some_elements(), 4)))
            running ._test_additive_associativity() . . . pass
            running ._test_an_element() . . . pass
            running ._test_cardinality() . . . pass
            running ._test_category() . . . pass
            running ._test_elements() . . .
              Running the test suite of self.an_element()
              running ._test_category() . . . pass
              running ._test_eq() . . . pass
              running ._test_nonzero_equal() . . . pass
              running ._test_not_implemented_methods() . . . pass
              running ._test_pickling() . . . pass
              pass
            running ._test_elements_eq_reflexive() . . . pass
            running ._test_elements_eq_symmetric() . . . pass
            running ._test_elements_eq_transitive() . . . pass
            running ._test_elements_neq() . . . pass
            running ._test_eq() . . . pass
            running ._test_not_implemented_methods() . . . pass
            running ._test_pickling() . . . pass
            running ._test_some_elements() . . . pass
            running ._test_zero() . . . pass

        .. SEEALSO::

            :doc:`k-regular sequence <k_regular_sequence>`,
            :class:`kRegularSequence`.
        """
        self.k = k
        super(kRegularSequenceSpace, self).__init__(*args, **kwds)


    def __reduce__(self):
        r"""
        Pickling support.

        TESTS::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: loads(dumps(Seq2))  # indirect doctest
            Space of 2-regular sequences over Integer Ring
        """
        return _pickle_kRegularSequenceSpace, \
            (self.k, self.coefficients(), self.category())


    def _repr_(self):
        r"""
        Return a representation string of this `k`-regular sequence space.

        OUTPUT:

        A string.

        TESTS::

            sage: repr(kRegularSequenceSpace(2, ZZ))  # indirect doctest
            'Space of 2-regular sequences over Integer Ring'
        """
        return 'Space of {}-regular sequences over {}'.format(self.k, self.base())


    def _n_to_index_(self, n):
        r"""
        Convert `n` to an index usable by the underlying
        recognizable series.

        INPUT:

        - ``n`` -- a nonnegative integer.

        OUTPUT:

        A word.

        TESTS::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: Seq2._n_to_index_(6)
            word: 011
            sage: Seq2._n_to_index_(-1)
            Traceback (most recent call last):
            ...
            OverflowError: can't convert negative value to unsigned char
        """
        from sage.rings.integer_ring import ZZ
        n = ZZ(n)
        W = self.indices()
        return W(n.digits(self.k))


    def _element_constructor_(self, *args, **kwds):
        element = super(kRegularSequenceSpace, self)._element_constructor_(*args, **kwds)

        from sage.rings.integer_ring import ZZ
        if element.mu[ZZ(0)] * element.right != element.right:
            import logging
            logger = logging.getLogger(__name__)
            print element.mu[ZZ(0)], element.right, element.mu[ZZ(0)] * element.right
            logger.warning('mu[0]*right != right')

        return element


    def guess(self, f, n_max=None, d_max=None, domain=None, sequence=None):
        r"""

        EXAMPLES:

        Binary sum of digits::

            sage: @cached_function
            ....: def s(n):
            ....:     if n == 0:
            ....:         return 0
            ....:     return s(n//2) + ZZ(is_odd(n))
            sage: all(s(n) == sum(n.digits(2)) for n in srange(10))
            True
            sage: [s(n) for n in srange(10)]
            [0, 1, 1, 2, 1, 2, 2, 3, 1, 2]

        Variant 1::

            sage: Seq2 = kRegularSequenceSpace(2, ZZ)
            sage: import logging
            sage: logging.basicConfig(level=logging.INFO)
            sage: S1 = Seq2.guess(s)
            INFO:...:including f_{1*m+0}
            INFO:...:M_0: f_{2*m+0} = (1) * X_m
            INFO:...:including f_{2*m+1}
            INFO:...:M_1: f_{2*m+1} = (0, 1) * X_m
            INFO:...:M_0: f_{4*m+1} = (0, 1) * X_m
            INFO:...:M_1: f_{4*m+3} = (-1, 2) * X_m
            sage: S1
            2-regular sequence 0, 1, 1, 2, 1, 2, 2, 3, 1, 2, ...
            sage: S1.mu[0], S1.mu[1], S1.left, S1.right
            (
            [1 0]  [ 0  1]
            [0 1], [-1  2], (1, 0), (0, 1)
            )
            sage: logging.shutdown(); _ = reload(logging)

        Variant 2::

            sage: C = Seq2((Matrix([[1]]), Matrix([[1]])), vector([1]), vector([1])); C
            2-regular sequence 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ...
            sage: S2 = Seq2.guess(s, sequence=C)
            sage: S2
            2-regular sequence 0, 1, 1, 2, 1, 2, 2, 3, 1, 2, ...
            sage: S2.mu[0], S2.mu[1], S2.left, S2.right
            (
            [1 0]  [1 0]
            [0 1], [1 1], (0, 1), (1, 0)
            )

        The sequence of all natural numbers::

            sage: S = Seq2.guess(lambda n: n)
            sage: S
            2-regular sequence 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ...
            sage: S.mu[0], S.mu[1], S.left, S.right
            (
            [2 0]  [ 0  1]
            [2 1], [-2  3], (1, 0), (0, 1)
            )

        The indicator function of the even integers::

            sage: S = Seq2.guess(lambda n: ZZ(is_even(n)))
            sage: S
            2-regular sequence 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, ...
            sage: S.mu[0], S.mu[1], S.left, S.right
            (
            [0 1]  [0 0]
            [0 1], [0 1], (1, 0), (1, 1)
            )

        The indicator function of the odd integers::

            sage: S = Seq2.guess(lambda n: ZZ(is_odd(n)))
            sage: S
            2-regular sequence 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, ...
            sage: S.mu[0], S.mu[1], S.left, S.right
            (
            [0 0]  [0 1]
            [0 1], [0 1], (1, 0), (0, 1)
            )

        TESTS::

            sage: S = Seq2.guess(lambda n: 2, sequence=C)
            sage: S
            2-regular sequence 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, ...
            sage: S.mu[0], S.mu[1], S.left, S.right
            ([1], [1], (2), (1))

        We guess some partial sums sequences::

            sage: S = Seq2((Matrix([1]), Matrix([2])), vector([1]), vector([1]))
            sage: S
            2-regular sequence 1, 2, 2, 4, 2, 4, 4, 8, 2, 4, ...
            sage: from itertools import islice
            sage: L = []; ps = 0
            sage: for s in islice(S, 110):
            ....:     ps += s
            ....:     L.append(ps)
            sage: G = Seq2.guess(lambda n: L[n])
            sage: G
            2-regular sequence 1, 3, 5, 9, 11, 15, 19, 27, 29, 33, ...
            sage: G.mu[0], G.mu[1], G.left, G.right
            (
            [ 0  1]  [3 0]
            [-3  4], [3 2], (1, 0), (1, 1)
            )
            sage: G == S.partial_sums(include_n=True)
            True

        ::

            sage: Seq3 = kRegularSequenceSpace(3, QQ)
            sage: S = Seq3((Matrix([1]), Matrix([3]), Matrix([2])), vector([1]), vector([1]))
            sage: S
            3-regular sequence 1, 3, 2, 3, 9, 6, 2, 6, 4, 3, ...
            sage: from itertools import islice
            sage: L = []; ps = 0
            sage: for s in islice(S, 110):
            ....:     ps += s
            ....:     L.append(ps)
            sage: G = Seq3.guess(lambda n: L[n])
            sage: G
            3-regular sequence 1, 4, 6, 9, 18, 24, 26, 32, 36, 39, ...
            sage: G.mu[0], G.mu[1], G.mu[2], G.left, G.right
            (
            [ 0  1]  [18/5  2/5]  [ 6  0]
            [-6  7], [18/5 27/5], [24  2], (1, 0), (1, 1)
            )
            sage: G == S.partial_sums(include_n=True)
            True
        """
        import logging
        logger = logging.getLogger(__name__)

        from sage.arith.srange import srange, xsrange
        from sage.matrix.constructor import Matrix
        from sage.misc.mrange import cantor_product
        from sage.modules.free_module_element import vector

        k = self.k
        if n_max is None:
            n_max = 100
        if d_max is None:
            d_max = 10
        if domain is None:
            domain = self.base()  # TODO
        if sequence is None:
            mu = [[] for _ in srange(k)]
            seq = lambda m: tuple()
        else:
            mu = [M.rows() for M in sequence.mu]
            seq = lambda m: sequence.left * sequence._mu_of_word_(
                self._n_to_index_(m))

        zero = domain(0)
        one = domain(1)

        def values(m, lines):
            return tuple(seq(m)) + tuple(f(k**t_R * m + r_R) for t_R, r_R, s_R in lines)

        @cached_function(key=lambda lines: len(lines))  # we assume that existing lines are not changed (we allow appending of new lines)
        def some_inverse_U_matrix(lines):
            d = len(seq(0)) + len(lines)

            for m_indices in cantor_product(xsrange(n_max), repeat=d, min_slope=1):
                U = Matrix(domain, d, d, [values(m, lines) for m in m_indices]).transpose()
                try:
                    return U.inverse(), m_indices
                except ZeroDivisionError:
                    pass
            else:
                raise RuntimeError

        def guess_linear_dependence(t_L, r_L, lines):
            iU, m_indices = some_inverse_U_matrix(lines)
            X_L = vector(f(k**t_L * m + r_L) for m in m_indices)
            return X_L * iU

        def verify_linear_dependence(t_L, r_L, linear_dependence, lines):
            return all(f(k**t_L * m + r_L) ==
                       linear_dependence * vector(values(m, lines))
                       for m in xsrange(0, (n_max - r_L) // k**t_L + 1))

        def find_linear_dependence(t_L, r_L, lines):
            linear_dependence = guess_linear_dependence(t_L, r_L, lines)
            if not verify_linear_dependence(t_L, r_L, linear_dependence, lines):
                raise ValueError
            return linear_dependence

        left = None
        if seq(0):
            try:
                solution = find_linear_dependence(0, 0, [])
            except ValueError:
                pass
            else:
                left = vector(solution)

        to_branch = []
        lines = []
        def include(line):
            to_branch.append(line)
            lines.append(line)
            t, r, s = line
            logger.info('including f_{%s*m+%s}', k**t, r)

        if left is None:
            line_L = (0, 0, 0)  # entries (t, r, s) --> k**t * m + r, belong to M_s
            include(line_L)
            left = vector((len(seq(0)) + len(lines)-1)*(zero,) + (one,))

        while to_branch:
            line_R = to_branch.pop(0)
            t_R, r_R, s_R = line_R
            if t_R >= d_max:
                raise RuntimeError

            t_L = t_R + 1
            for s_L in srange(k):
                r_L = k**t_R * s_L + r_R
                line_L = t_L, r_L, s_L

                try:
                    solution = find_linear_dependence(t_L, r_L, lines)
                except ValueError:
                    include(line_L)
                    solution = (len(lines)-1)*(zero,) + (one,)
                logger.info('M_%s: f_{%s*m+%s} = %s * X_m',
                            s_L, k**t_L, r_L, solution)
                mu[s_L].append(solution)

        d = len(seq(0)) + len(lines)
        mu = tuple(Matrix(domain, [pad_right(tuple(row), d, zero=zero) for row in M])
                         for M in mu)
        right = vector(values(0, lines))
        left = vector(pad_right(tuple(left), d, zero=zero))
        return self(mu, left, right)
