import sys
from copy import deepcopy
from math import isclose
from decimal import Decimal
from fractions import Fraction

try:
    from utils import convert_version
except ModuleNotFoundError:
    from .utils import convert_version


# === Distribution ============================================================

# --- Fractions ---------------------------------------------------------------

fractions__0_1 = {

    # original
    'original': {
        'fraction': 1,
        'split': {
            'copyright': {
                'fraction': Fraction(9, 12),
                'split': {
                    'composition': {
                        'fraction': Fraction(2, 3),
                    },
                    'lyrics': {
                        'fraction': Fraction(1, 3),
                    },
                },
            },
            'ancillary': {
                'fraction': Fraction(3, 12),
                'split': {
                    'performance': {
                        'fraction': Fraction(5, 6),
                    },
                    'production': {
                        'fraction': Fraction(1, 6),
                    },
                },
            },
        },
    },

    # adaption
    'adaption': {
        'fraction': 1,
        'split': {
            'copyright': {
                'fraction': Fraction(7, 12),
                'split': {
                    'composition': {
                        'fraction': Fraction(2, 3),
                    },
                    'lyrics': {
                        'fraction': Fraction(1, 3),
                    },
                },
            },
            'ancillary': {
                'fraction': Fraction(3, 12),
                'split': {
                    'performance': {
                        'fraction': Fraction(5, 6),
                    },
                    'production': {
                        'fraction': Fraction(1, 6),
                    },
                },
            },
            'derivative': {
                'fraction': Fraction(2, 12),
            },
        },
    },

    # remix
    'remix': {
        'fraction': 1,
        'split': {
            'originals': {
                'fraction': Fraction(6, 12),
                'distribution': 'original',
            },
            'copyright': {
                'fraction': Fraction(2, 12),
            },
            'ancillary': {
                'fraction': Fraction(4, 12),
                'split': {
                    'performance': {
                        'fraction': Fraction(4, 6),
                    },
                    'remix_production': {
                        'fraction': Fraction(2, 6),
                    },
                },
            },
        },
    },

}

fractions__0_2 = fractions__0_1
fractions__0_3 = fractions__0_1


# --- Roles -------------------------------------------------------------------

def roles__0_1(utilisation, creation):

    # distribution
    roles = {
        'plan': utilisation.distribution_plan.version,
        'type': creation.distribution_type,
        'creation': creation.code,
        'meta': {
            'utilisation': utilisation.code,
        },
    }

    # split original
    if creation.distribution_type == 'original':
        roles['split'] = {
            'copyright': {
                'composition': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='copyright',
                        contribution='composition'
                    ),
                },
                'lyrics': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='copyright',
                        contribution='lyrics'
                    ),
                },
            },
            'ancillary': {
                'performance': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='instrument'
                    ),
                },
                'production': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='production'
                    ),
                },
            },
        }

    # split cover
    elif creation.distribution_type == 'cover':
        original = creation.original_relations[0].original_creation
        roles['type'] = 'original'
        roles['split'] = {
            'copyright': {
                'composition': {
                    'rightsholders': original.get_rightsholders(
                        right_type='copyright',
                        contribution='composition'
                    ),
                },
                'lyrics': {
                    'rightsholders': original.get_rightsholders(
                        right_type='copyright',
                        contribution='lyrics'
                    ),
                },
            },
            'ancillary': {
                'performance': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='instrument'
                    ),
                },
                'production': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='production'
                    ),
                },
            },
        }

    # split adaption
    elif creation.distribution_type == 'adaption':
        original = creation.original_relations[0].original_creation
        roles['split'] = {
            'copyright': {
                'composition': {
                    'rightsholders': original.get_rightsholders(
                        right_type='copyright',
                        contribution='composition'
                    ),
                },
                'lyrics': {
                    'rightsholders': original.get_rightsholders(
                        right_type='copyright',
                        contribution='lyrics'
                    ),
                },
            },
            'ancillary': {
                'performance': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='instrument'
                    ),
                },
                'production': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='production'
                    ),
                },
            },
            'derivative': {
                'rightsholders': creation.get_rightsholders(
                    right_type='copyright',
                    contribution='composition'
                ) + creation.get_rightsholders(
                    right_type='copyright',
                    contribution='lyrics'
                ),
            },
        }

    # split remix
    elif creation.distribution_type == 'remix':
        originals = [cor.original_creation
                     for cor in creation.original_relations]
        roles['split'] = {
            'originals': [{
                'plan': utilisation.distribution_plan.version,
                'type': 'original',
                'creation': creation.code,
                'meta': {
                    'utilisation': utilisation.code,
                },
                'split': {
                    'copyright': {
                        'composition': {
                            'rightsholders': original.get_rightsholders(
                                right_type='copyright',
                                contribution='composition'
                            ),
                        },
                        'lyrics': {
                            'rightsholders': original.get_rightsholders(
                                right_type='copyright',
                                contribution='lyrics'
                            ),
                        },
                    },
                    'ancillary': {
                        'performance': {
                            'rightsholders': original.get_rightsholders(
                                right_type='ancillary',
                                contribution='instrument'
                            ),
                        },
                        'production': {
                            'rightsholders': original.get_rightsholders(
                                right_type='ancillary',
                                contribution='production'
                            ),
                        },
                    },
                },
            } for original in originals],
            'copyright': {
                'rightsholders': creation.get_rightsholders(
                    right_type='copyright',
                    contribution='composition'
                ) + creation.get_rightsholders(
                    right_type='copyright',
                    contribution='lyrics'
                ),
            },
            # remix: ancillary: production, mixin, mastering
            'ancillary': {
                'performance': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='instrument'
                    ),
                },
                'remix_production': {
                    'rightsholders': creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='production'
                    ) + creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='mixing'
                    ) + creation.get_rightsholders(
                        right_type='ancillary',
                        contribution='mastering'
                    ),
                },
            },
        }

    # split invalid
    else:
        raise ValueError(
            f"unkown distribution type '{creation.distribution_type}' for "
            f"creation: {creation}")

    return [roles]


roles__0_2 = roles__0_1
roles__0_3 = roles__0_1


# --- Split -------------------------------------------------------------------

class Rightsholder():
    """
    Represents a rigthsholder in a Split tree.

    Args:
        licenser (obj): the licenser
        fraction (dict): the fraction of the amount
        amount (Decimal): optional - the amount for the licenser
    """
    def __init__(self, licenser, fraction, amount=None):
        self.licenser = licenser
        self.fraction = fraction
        self.amount = amount

    def print(self, level=1):
        """
        Prints the state of the rightsholder.
        """
        output = f"- {self.fraction} {self.licenser}".ljust(40-level*2)
        if self.amount:
            output += f"{self.amount:.40f}".rjust(50)
        output += "\n"
        if level > 1:
            return output
        print(output)


class Split():
    """
    Helper class to distribute money among rightsholders.

    This class generates a tree of role splits and rightsholder leaves to
    distribute an amount of money to. Roles containing no rightsholders are
    redistributed among its siblings relative to their weights. The
    redistribution starts at the leaves and ends at the root node and operates
    on the node fraction.Fractions. On distribution, a decimals.Decimal amount
    is distributed with respect to the fractions.

    There are many checks in place to ensure the correctness of the
    calculations for both redistribution and distribution as well as to ensure,
    that the role structure matches the distribution plan.

    The init expects two dictionaries:

    - fractions: a dictionary with a definition of the available roles and
        their split fractions according to the distribution plan, e.g.
    - roles: a dictionary mapping rightsholders to the roles given in fractions

    Args:
        roles (dict): the mapping of rightsholders to roles
        amount (Decimal): optional - the amount to distribute
        fractions (dict): the mapping of roles to fractions

        key (str): the key of the tree node
        parent (Split): the parent of the tree node

        redistribute (bool): redistribute fractions of nodes without
          rightsholders after init
        log (bool): log each redistribution
        debug (bool): debug flag to print the final state of the tree
        verbose (bool): debug flag for more verbose prints of redistributions

    Returns:
        a list of dictionaries for each rightsholder, e.g.

        [
            {
                'licenser': licenser1
                'amount': Decimal('1234.56')
                'meta': {
                    'creation': 'C00001',
                    'utilisation': 'U00001',
                },
            },
            {
                'licenser': licenser2
                'amount': Decimal('6543.21')
                'meta': {
                    'creation': 'C00002',
                    'utilisation': 'U00001',
                    'redistributed': 'root.role1'
                },
            },
        ]

    Attributes:
        key (str): key of the tree node
        parent (Split): parent of the tree node

        fraction (fractions.Fraction): fraction for the split
        initial_fraction (fractions.Fraction): initial fraction for the split
        amount (Decimal): amount to be splitted

        splits ([Split]): children of the tree node
        rightsholders ([Rightsholder]): rightsholders of a leave node

        reentry (bool): another full distribution type split (recursion)
        redistributed (bool): indicator, if the split was redistributed

        References to the next distribution split node:
            meta (dict): meta information passed to the returned share list
            creation (str): creation identifier,
            distribution_plan (str): version of the distribution plan
            distribution_type (str): type of the distribution

        References to the root node:
            config (dict): configuration flags
            log (list): distribution log

    Raises:
        AssertionError:
          - key contains a dot
          - distribution nodes contain other non-distribution nodes
          - mismatch between roles and fraction hierarchy
          - sum of split/rightsholder fractions/amounts don't add up
          - no rightsholders in the whole tree

    Fractions:
        The fraction dict structure:

            fractions = {
                '<DISTRIBUTION_TYPE_1>': {
                    'fraction': fractions.Fraction(),
                    'split': {
                        '<ROLENAME_1>': {
                            'fraction': fractions.Fraction(),
                            'split': {
                                '<ROLENAME_2>': {
                                    'fraction': fractions.Fraction(),
                                    'split': [...]
                                },
                                '<ROLENAME_3>': {
                                    'fraction': fractions.Fraction(),
                                },
                                [...]
                            },
                        },
                        '<ROLENAME_4>': {
                            'fraction': fractions.Fraction(),
                            'split': [...]
                        },
                        '<ROLENAME_5>': {
                            'fraction': fractions.Fraction(),
                            'distribution': '<DISTRIBUTION_NAME_1>'
                        },
                        [...]
                    },
                },
            }

        The first level of the fractions defines the available distribution
        types given by the distribution plan (e.g. 'original', 'adaption',
        'remix'). All other levels

        - must define a 'fraction'
        - may contain either
            - another 'split'
            - or a 'distribution'

        Notes:
          - If only 'fraction' is defined, the role represents a split among
            rightsholders (leaves). By default the amount is split evenly.
          - If 'split' is defined, the role represents a split among other
            split nodes (non-leaves).
          - If 'distribution' is defined, the role represents another full
            distribution node (recursion). The distribution name must exist
            in the fractions definition. By default the amount is split evenly.
          - The first level of a Split must be a distribution node.

        The fraction dict must be defined in the distribution module
        and must have the name 'fraction__<DISTRIBUTION_PLAN>', e.g.
        'fraction__0_1 = {...}' in order to support dynamic choice of
        different distribution plan versions in one run.

    Roles:
        The roles dict structure:

            roles = [
                {
                    'plan': '<DISTRIBUTION_PLAN_1>',
                    'type': '<DISTRIBUTION_TYPE_1>',
                    'creation': '<CREATION_IDENTIFIER_1>',
                    'meta': {
                        '<KEY_1>': <VALUE_1>,
                        '<KEY_2>': <VALUE_2>,
                    },
                    'split': {
                        '<ROLENAME_1>': {
                            'rightsholders': [
                                <RIGHTSHOLDER_1>,
                                <RIGHTSHOLDER_2>,
                                [...]
                            ],
                        },
                        '<ROLENAME_2>': {
                            '<ROLENAME_3>': {
                                'rightsholders': [
                                    <RIGHTSHOLDER_3>,
                                    <RIGHTSHOLDER_4>,
                                    [...]
                                ],
                            },
                            [...]
                        },
                        '<ROLENAME_4>': {
                            'rightsholders': [
                                {
                                    'licensee': <RIGHTSHOLDER_5>,
                                    'fraction': fractions.Fraction()
                                }
                                {
                                    'licensee': <RIGHTSHOLDER_6>,
                                    'fraction': fractions.Fraction()
                                }
                                [...]
                            ],
                        },
                        '<ROLENAME_5>': [
                            {
                                'plan': '<DISTRIBUTION_PLAN_2>',
                                'type': '<DISTRIBUTION_TYPE_2>',
                                'creation': '<CREATION_IDENTIFIER_2>',
                                'meta': {},
                                'split': [...]
                            }, {
                                'plan': '<DISTRIBUTION_PLAN_3>',
                                'type': '<DISTRIBUTION_TYPE_3>',
                                'creation': '<CREATION_IDENTIFIER_3>',
                                'meta': {},
                                'split': [...]
                            }
                        ],
                        [...]
                    },
                },
                [...]
            ]

        The first level of the roles defines a list of distribution nodes with
        all information needed to pick the right fractions.

        Distribution Node:
            plan (str): the distribution plan verion
            type (str): the distribution type for the split
            creation (str): arbitrary identifier for the creation
            meta (dict): arbitrary meta infos passed to the returned share list
            split (dict): mapping from roles to rightsholders, must match the
              structure of the fractions of the distrbution

        Depending on the fractions, the 'split' need to have different forms:

            - Only '<ROLENAME>' defined for splits among other split nodes

                {
                    '<ROLENAME>': [...],
                }

            - Only 'rightsholders' defined for leave nodes

                {
                    'rightsholders': [
                        <RIGHTSHOLDER_1>,
                        <RIGHTSHOLDER_2>,
                        {
                            'licenser': <RIGHTSHOLDER_3>,
                            'fraction': fractions.Fraction(),
                        }
                    ],
                }

              which must contain a (possibly empty) list of rightsholders.
              The list might contain the rightsholder object (arbitrary, but no
              dicts), or a dict with 'licenser' and 'fraction', to be able to
              change the default of even distribution (if given by contracts).
              Note: All fractions of a level must equal 1.

            - A list of new distributions for distribution nodes (recursion).
              For a definition see "distribution node" above.

    Example:
        >>> import distribution
        >>> from fractions import Fraction
        >>> distribution.fractions__0_0_1 = {
        ...     'original': {
        ...         'fraction': 1,
        ...         'split': {
        ...             'copyright': {
        ...                 'fraction': Fraction(1, 2),
        ...             },
        ...             'ancillary': {
        ...                 'fraction': Fraction(1, 2),
        ...             },
        ...         },
        ...     },
        ... }
        >>> roles = [{
        ...    'plan': '0.0.1',
        ...    'type': 'original',
        ...    'creation': 'C00001',
        ...    'meta': {'utilisation': 'U00001'},
        ...    'split': {
        ...        'copyright': {
        ...            'rightsholders': ['licenser1', 'licenser2'],
        ...        },
        ...        'ancillary': {
        ...            'rightsholders': ['licenser3', 'licenser4'],
        ...        },
        ...    },
        ... }]
        >>> split = distribution.Split(roles)
        >>> split.distribute(Decimal(1000))
        ... [{'amount': Decimal('250'),
        ...   'licenser': 'licenser1',
        ...   'meta': {'redistributed': [], 'utilisation': 'U00001'}},
        ...  {'amount': Decimal('250'),
        ...   'licenser': 'licenser2',
        ...   'meta': {'redistributed': [], 'utilisation': 'U00001'}},
        ...  {'amount': Decimal('250'),
        ...   'licenser': 'licenser3',
        ...   'meta': {'redistributed': [], 'utilisation': 'U00001'}},
        ...  {'amount': Decimal('250'),
        ...   'licenser': 'licenser4',
        ...   'meta': {'redistributed': [], 'utilisation': 'U00001'}}]

        >>> roles = [{
        ...    'plan': '0.0.1',
        ...    'type': 'original',
        ...    'creation': 'C00001',
        ...    'meta': {'utilisation': 'U00001'},
        ...    'split': {
        ...        'copyright': {
        ...            'rightsholders': ['licenser1', 'licenser2'],
        ...        },
        ...        'ancillary': {
        ...            'rightsholders': [],
        ...        },
        ...    },
        ... }]
        >>> split = distribution.Split(roles)
        >>> split.distribute(Decimal(1000))
        ... [{'amount': Decimal('500'),
        ...   'licenser': 'licenser1',
        ...   'meta': {'redistributed': ['root.C00001.copyright'],
        ...            'utilisation': 'U00001'}},
        ...  {'amount': Decimal('500'),
        ...   'licenser': 'licenser2',
        ...   'meta': {'redistributed': ['root.C00001.copyright'],
        ...            'utilisation': 'U00001'}}]

        >>> roles = [{
        ...    'plan': '0.0.1',
        ...    'type': 'original',
        ...    'creation': 'C00001',
        ...    'meta': {'utilisation': 'U00001'},
        ...    'split': {
        ...        'copyright': {
        ...            'rightsholders': [
        ...                {
        ...                    'licenser': 'licenser1',
        ...                    'fraction': Fraction(2, 3)],
        ...                }, {
        ...                    'licenser': 'licenser2',
        ...                    'fraction': Fraction(1, 3)],
        ...                },
        ...            ],
        ...        },
        ...        'ancillary': {
        ...            'rightsholders': [],
        ...        },
        ...    },
        ... }]
        >>> split = distribution.Split(roles)
        >>> split.distribute(Decimal(1000))
        ... [{'amount': Decimal('666.6666666666666666666666667'),
        ...   'licenser': 'licenser1',
        ...   'meta': {'redistributed': ['root.C00001.copyright'],
        ...            'utilisation': 'U00001'}},
        ...  {'amount': Decimal('333.3333333333333333333333333'),
        ...   'licenser': 'licenser2',
        ...   'meta': {'redistributed': ['root.C00001.copyright'],
        ...            'utilisation': 'U00001'}}]

    """

    # --- Behaviour -----------------------------------------------------------

    def __init__(self, roles, amount=None, fractions={},
                 key='root', parent=None,
                 redistribute=True, log=True, debug=False, verbose=False):
        assert "." not in key, "dot is not allowed in keys"
        self.key = key
        self.parent = parent

        self.fraction = fractions and fractions['fraction'] or Fraction(1)
        self.initial_fraction = self.fraction
        self.amount = amount

        self.splits = []
        self.rightsholders = []

        self.reentry = False
        self.redistributed = False

        self._meta = None
        self._creation = None
        self._distribution_plan = None
        self._distribution_type = None
        if isinstance(roles, dict) and 'split' in roles:
            distribution = roles
            self._meta = distribution.get('meta', {})
            self._creation = distribution['creation']
            self._distribution_plan = distribution['plan']
            self._distribution_type = distribution['type']
            roles = distribution['split']
            version = convert_version(self._distribution_plan)
            all_fractions = getattr(
                sys.modules[__name__], f"fractions__{version}")
            fractions = all_fractions[self.distribution_type]

        if self.is_root():
            self._config = {
                'log': log,
                'debug': debug,
                'verbose': verbose,
            }
            self._log = []

        # new distribution
        if isinstance(roles, list):
            distributions = roles
            assert all(['split' in distribution
                        for distribution in distributions]), (
                f"{roles} does not contain only distributions")
            if not self.is_root():
                for distribution in distributions:
                    assert distribution['type'] == fractions['distribution'], (
                        f"distribution type '{distribution['type']}' "
                        f"of {self.path}.{distribution['creation']} does not "
                        f"match the type '{fractions['distribution']}' "
                        f"expected in the fractions of the distribution plan "
                        f"{self.root.distribution_plan}")
            num_distributions = len(distributions)
            if not num_distributions:
                return
            fraction = Fraction(1, num_distributions)
            for distribution in distributions:
                fractions = deepcopy(fractions)
                fractions['fraction'] = distribution.get('fraction', fraction)
                creation = Split(roles=distribution,
                                 fractions=fractions,
                                 key=distribution['creation'],
                                 parent=self)
                creation.reentry = True
                self.splits.append(creation)
                if self.config['debug']:
                    self.__dict__[distribution['creation']] = creation

            # verify that all fractions equal 1
            assert self.fraction_sum == 1, (
                f"sums of split fractions in {self.path} don't equal 1")

            # postprocessig after tree generation
            if self.is_root():
                # debug
                if self.config['debug']:
                    print("=" * 86)
                    if not self.contains_rightsholders():
                        print()
                        self.print()
                if self.config['debug'] and self.config['verbose']:
                    self.print('initial')
                # redistribute leaves without rightsholders
                if redistribute:
                    self.redistribute()
                # distribute amount
                if amount:
                    self.distribute(amount)
            return

        # leave nodes with rightsholders
        if 'rightsholders' in roles:
            assert 'split' not in fractions, (
                f"rightsholders given in:\n{roles}\n "
                f"but split expected in\n{fractions}")
            num_rightsholders = len(roles['rightsholders'])
            if not num_rightsholders:
                return
            even_fraction = Fraction(1, num_rightsholders)
            for rightsholder in roles['rightsholders']:
                licenser = rightsholder
                fraction = even_fraction
                if isinstance(rightsholder, dict):
                    if 'fraction' in rightsholder:
                        fraction = rightsholder['fraction']
                    licenser = rightsholder['licenser']
                self.rightsholders.append(
                    Rightsholder(
                        licenser=licenser,
                        fraction=fraction,
                    )
                )
            assert self.fraction_sum == 1, (
                f"sums of rightsholder fractions in {self.path} don't equal 1")
            return

        # non leave nodes with a further split
        for key in roles:
            split = Split(roles=roles[key],
                          fractions=fractions['split'][key],
                          key=key,
                          parent=self)
            self.splits.append(split)
            if self.config['debug']:
                self.__dict__[key] = split

        # verify that all fractions equal 1
        assert self.fraction_sum == 1, (
            f"sums of split fractions in {self.path} don't equal 1")

    def __contains__(self, item):
        for split in self.splits:
            if item == split.key:
                return True
        return False

    def __getitem__(self, key):
        for split in self.splits:
            if key == split.key:
                return split
        raise KeyError(f"split {key} not found in {self.path}")

    def __iter__(self):
        return iter(self.splits[::-1])

    def __len__(self):
        return len(self.splits)

    def __str__(self):
        return f"{self.key}"

    def __repr__(self):
        attributes = f"path={self.path}"
        attributes += f" splits={[split.key for split in self.splits]}"
        attributes += f" fraction={self.fraction}"
        if self.amount:
            attributes += f" amount={self.amount}"
        return (f"<Split {attributes}>")

    # --- Actions -------------------------------------------------------------

    def redistribute(self):
        """
        Reverse recursive redistribution of split fractions without
        rightsholders.
        """
        # redistribute
        for role in self.pre_leaves:
            role._redistribute()

    def _redistribute(self):
        # redirect to first pre leave
        if self.is_leaf():
            self.parent._redistribute()
            return

        # redistribute
        for source_split in self.splits:
            distribution_before = self.distribution

            # ignore leaves with rightsholders
            if source_split.is_leaf() and source_split.rightsholders:
                continue
            # ignore non leaves with positive fraction sum
            if not source_split.is_leaf() and source_split.fraction_sum != 0:
                continue

            # redistribute
            for target_split in self.splits:
                if target_split == source_split:
                    continue
                if not target_split.fraction:
                    continue
                target_split.fraction /= 1 - source_split.fraction
                target_split.redistributed = True
            source_split.fraction = 0
            source_split.redistributed = True

            # verify that all fractions equal 0 or 1
            assert self.fraction_sum in [0, 1], (
                f"sums of split fractions in {self.path} don't equal 0 or 1")

            # log
            if self.config['log']:
                self.log.append({
                    "type": "redistribution",
                    "path": source_split.path,
                    "before": distribution_before,
                    "after": self.distribution})
            # debug
            if self.config['debug'] and self.config['verbose']:
                self.print(f'redistribution: {source_split.path}')

        # redistribute parent
        if not self.is_root():
            self.parent._redistribute()

    def distribute(self, amount):
        """
        Distribution of an amount among the splits.
        """
        # ensure at least one rightsholder exists to distribute to
        assert self.contains_rightsholders(), (
          "the provided rightsholders list contain no rightsholders")
        # distribute
        self.amount = amount
        self._distribute()
        if self.config['debug']:
            self.print(f'distribution: {amount}')
        assert isclose(self.amount,
                       sum([rightsholder.amount
                            for rightsholder in self.all_rightsholders
                            if rightsholder.amount])), (
               f"sum of rightsholder amounts not equal to amount in {self}")
        licenser_shares = self.licenser_shares
        assert isclose(self.amount,
                       sum([share['amount']
                            for share in licenser_shares
                            if share['amount']])), (
               f"sum of licenser share amounts not equal to amount in {self}")
        return licenser_shares

    def _distribute(self):
        if not self.amount:
            return
        for split in self.splits:
            split.amount = (
                self.amount
                * Decimal(split.fraction.numerator)
                / Decimal(split.fraction.denominator)
            )
            if not split.is_leaf():
                split._distribute()
                continue
            for rightsholder in split.rightsholders:
                rightsholder.amount = (
                    split.amount
                    * Decimal(rightsholder.fraction.numerator)
                    / Decimal(rightsholder.fraction.denominator)
                )

    def print(self, msg="", level=1):
        """
        Prints the state of the tree.
        """
        output = ""
        if msg:
            output += f"\n{msg}\n" + "-" * 86 + "\n"
        reentry = self.reentry and "> " or ""
        output += f"{self.fraction} {reentry}{self.key}".ljust(38-level*2)
        if self.amount:
            output += f"{self.amount:.40f}".rjust(50)
        output += "\n"
        for split in self.splits:
            output += "  " * level + split.print(level=level + 1)
        for rightsholder in self.rightsholders:
            output += "  " * level + rightsholder.print(level=level + 2)
        if level > 1:
            return output
        print(output)

    # --- Domain --------------------------------------------------------------

    @property
    def licenser_shares(self):
        """
        Generates a list of licenser shares from the current state of the tree.
        """
        if self.is_leaf():
            shares = []
            for rightsholder in self.rightsholders:
                meta = self.meta.copy()
                meta['creation'] = self.creation
                meta['redistributed'] = self.redistributed_roles
                shares.append({
                    'licenser': rightsholder.licenser,
                    'amount': rightsholder.amount,
                    'meta': meta,
                })
            return shares
        return sum([split.licenser_shares for split in self.splits], [])

    @property
    def redistributed_roles(self):
        """
        Returns all redistributed roles along the path of the current node.
        """
        roles = []
        if self.redistributed:
            roles.append(self.path)
        if self.parent:
            roles.extend(self.parent.redistributed_roles)
        return roles

    @property
    def distribution(self):
        """
        Returns a simple dict of the fractions of the children splits.
        """
        return {split.key: split.fraction for split in self.splits}

    @property
    def fraction_sum(self):
        """
        Returns the sum of the fractions of the children splits.
        """
        if self.is_leaf():
            return sum([rightsholder.fraction
                        for rightsholder in self.rightsholders])
        return sum([split.fraction for split in self.splits])

    @property
    def all_rightsholders(self):
        """
        Returns rightsholders contained by the current branch including itself.
        """
        return [
            rightsholder
            for split in self.leaves
            for rightsholder in split.rightsholders
        ]

    @property
    def meta(self):
        """
        Returns meta of first distribution node among parents.
        """
        if self._meta:
            return self._meta
        if self.is_root():
            return None
        return self.parent.meta

    @property
    def creation(self):
        """
        Returns creation of first distribution node among parents.
        """
        if self._creation:
            return self._creation
        if self.is_root():
            return None
        return self.parent.creation

    @property
    def distribution_plan(self):
        """
        Returns distribution plan of first distribution node among parents.
        """
        if self._distribution_plan:
            return self._distribution_plan
        if self.is_root():
            return None
        return self.parent.distribution_plan

    @property
    def distribution_type(self):
        """
        Returns distribution type of first distribution node among parents.
        """
        if self._distribution_type:
            return self._distribution_type
        if self.is_root():
            return None
        return self.parent.distribution_type

    def contains_rightsholders(self):
        """
        Checks if the current branch including itself contains rightsholders.
        """
        if self.rightsholders:
            return True
        for split in self.splits:
            if split.contains_rightsholders():
                return True
        return False

    # --- Tree ----------------------------------------------------------------

    @property
    def root(self):
        """
        Returns the root node.
        """
        if self.is_root():
            return self
        return self.parent.root

    def is_root(self):
        """
        Checks if current node is the root node.
        """
        return self.parent is None

    @property
    def leaves(self):
        """
        Returns all leaves of the current branch starting from itself.
        """
        if self.is_leaf():
            return [self]
        return sum([split.leaves for split in self.splits], [])

    @property
    def pre_leaves(self):
        """
        Returns pre-leaves nodes of the current branch starting from itself
        (nodes with child leaves).
        """
        return set([leaf.parent for leaf in self.leaves])

    def is_leaf(self):
        """
        Checks if current node is a leaf.
        """
        return not self.splits

    @property
    def path(self):
        """
        Returns the current path in dot notation.
        """
        if self.is_root():
            return f"{self.key}"
        return f"{self.parent.path}.{self.key}"

    @property
    def config(self):
        """
        Returns the config dict of the root node.
        """
        if self.is_root():
            return self._config
        return self.parent.config

    @property
    def log(self):
        """
        Returns the log dict of the root node.
        """
        if self.is_root():
            return self._log
        return self.parent.log
