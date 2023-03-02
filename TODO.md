# Features and other enhancements on the road map

[ ] Handle multiple versions of the same class in `ManifestManager`
[ ] Add `metadata` field `skipApplyAll` (boolean value) to indicate to the `apply_command()` function in `src/py_animus/py_animus.py` if this manifest must be applied or not. A Value of `true` will skip over the manifest onto the next manifest
[ ] Add `metadata` field `applyOrderSequence` (integer value) to indicate to the `apply_command()` function in `src/py_animus/py_animus.py` if this manifest has to be applied in a certain order. Manifests with this field will be considered first, and applied from low to high numbers. Manifests with the same integer value will be processed in more-or-less random order. Manifests without this field will be processed afterwards in more-or-less random order.
