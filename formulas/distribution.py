import sys
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
    def __init__(self, licenser, fraction, amount=None):
        self.licenser = licenser
        self.fraction = fraction
        self.amount = amount

    def print(self, level=1):
        output = f"- {self.fraction} {self.licenser}".ljust(40-level*2)
        if self.amount:
            output += f"{self.amount:.40f}".rjust(50)
        output += "\n"
        if level > 1:
            return output
        print(output)


class Split():
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

        self._config = {
            'log': log,
            'debug': debug,
            'verbose': verbose,
        }
        if self.is_root():
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
                        f"of {self.path}.{distribution['creation']} does not"
                        f"match the type '{fractions['distribution']}' "
                        f"expected in the fractions of the distribution plan "
                        f"{self.root.distribution_plan}")
            fraction = Fraction(1, len(distributions))
            for distribution in distributions:
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

    # --- actions -------------------------------------------------------------

    def redistribute(self):
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
                            for rightsholder in self.all_rightsholders])), (
               f"sum of rightsholder amounts not equal to amount in {self}")
        licenser_shares = self.licenser_shares
        assert isclose(self.amount,
                       sum([share['amount']
                            for share in licenser_shares])), (
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

    # --- domain --------------------------------------------------------------

    @property
    def licenser_shares(self):
        if self.is_leaf():
            shares = []
            for rightsholder in self.rightsholders:
                meta = self.meta.copy()
                meta['creation']: self.creation
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
        roles = []
        if self.redistributed:
            roles.append(self.path)
        if self.parent:
            roles.extend(self.parent.redistributed_roles)
        return roles

    @property
    def distribution(self):
        return {split.key: split.fraction for split in self.splits}

    @property
    def fraction_sum(self):
        if self.is_leaf():
            return sum([rightsholder.fraction
                        for rightsholder in self.rightsholders])
        return sum([split.fraction for split in self.splits])

    @property
    def all_rightsholders(self):
        return [
            rightsholder
            for split in self.leaves
            for rightsholder in split.rightsholders
        ]

    @property
    def meta(self):
        if self._meta:
            return self._meta
        if self.is_root():
            return None
        return self.parent.meta

    @property
    def creation(self):
        if self._creation:
            return self._creation
        if self.is_root():
            return None
        return self.parent.creation

    @property
    def distribution_plan(self):
        if self._distribution_plan:
            return self._distribution_plan
        if self.is_root():
            return None
        return self.parent.distribution_plan

    @property
    def distribution_type(self):
        if self._distribution_type:
            return self._distribution_type
        if self.is_root():
            return None
        return self.parent.distribution_type

    def contains_rightsholders(self):
        if self.rightsholders:
            return True
        for split in self.splits:
            if split.contains_rightsholders():
                return True
        return False

    # --- tree ----------------------------------------------------------------

    @property
    def root(self):
        if self.is_root():
            return self
        return self.parent.root

    def is_root(self):
        return self.parent is None

    @property
    def leaves(self):
        if self.is_leaf():
            return [self]
        return sum([split.leaves for split in self.splits], [])

    @property
    def pre_leaves(self):
        return set([leaf.parent for leaf in self.leaves])

    def is_leaf(self):
        return not self.splits

    @property
    def path(self):
        if self.is_root():
            return f"{self.key}"
        return f"{self.parent.path}.{self.key}"

    @property
    def config(self):
        if self.is_root():
            return self._config
        return self.parent.config

    @property
    def log(self):
        if self.is_root():
            return self._log
        return self.parent.log

    # --- behaviour -----------------------------------------------------------

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
