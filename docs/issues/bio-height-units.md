# admitted bio height has no verified unit mapping

problem: the admitted bio normalization retains an integer `height` without a supported unit conversion. [03k's ledger](../research/features-03k/ledger.md) explicitly leaves its units unspecified; the optional card field requires centimeters. a plausible-looking value is not evidence of units.

impact: preserve raw height and its locator, but expose normalized `height_cm:null` with `unit_unverified`. identity, age, handedness, models and card completion do not depend on optional height. do not overwrite source integers or guess inches/centimeters.

owner: factual identity preparation and v1-03's optional card-identity reduction. resolve with an independently checked primary source/schema or explicit paired-unit evidence bound to the relevant feed/version, then verify conversion on admitted examples and retain any conflicting/missing cases. public documentation alone does not establish that a different historical feed used the same units. no acquisition or separate research campaign is assigned.
