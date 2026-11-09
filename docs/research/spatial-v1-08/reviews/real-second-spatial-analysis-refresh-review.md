# real second spatial annual: analysis pin refresh review

verdict: clear for root's separate year-two release. this review makes no launch. [previous concrete command review](real-second-spatial-final-pin-review.md) · [compositor cutover review](spatial-composition-concrete-pin-review.md)

| artifact | sha256 |
| --- | --- |
| `var/v1-08-replacement/real-20222023-spatial-command.sh` | `3fc512031d1b5418767d66db9ecb0d2fab1e4a1480d127bd6e7fb506d24665e9` |
| `var/v1-08-replacement/accept_real_spatial_20222023.py` | `490c33b839b51c59bfc39dbf640d40794d658d684759d0c4ba97b437676f3418` |
| `var/v1-08-replacement/real-20222023-spatial-analysis-refresh.json` | `b3537571a7dcd078d8a88ac62a77918d4244c4e9c323cc3453e1c92b0c31dda3` |
| compositor application receipt | `a164d4f438c273290db70c928c5b369a75b0506f05e00616d0cfc17c258100f5` |

each source file changes exactly one `fc716257eb118d1a091472cde4b214e8bca1f753` tree literal to `2866624de84c2f1a4881e9cee516db3f5530e3ba`. independently reversing that substitution reproduces previous command `a781f89394b0199e68ef3500dc6201779327da472080b2d73199fac2e85a484d` and helper `ca5f00ae790453af62b55078ffad1d14123d501aaddf0e547d170896282c8267` exactly. the ordinary argv, predecessor `3b7b5133`, score `296ae017`, recipe `04a9c15d`, native controls, guards, paths, resource reporting and helper logic are unchanged.

commit `8a5bd97fd9aed73e55ceddadf9ca156c581265e7` and current analysis both resolve to the new pinned tree. comparing the old and new analysis trees lists only `src/hockey_stats/spatial_composition.py`. installed compositor bytes equal reviewed candidate `d0d98be5c6c15a86b10945250d087b60164369df9e3887f00550eaf7f95008d6`; all three protected spatial numerical owners retain their reviewed hashes. analysis is clean. the application receipt, its reviewed patch/base bindings, the superseded preparation and current refresh reproduce their hashes.

`zsh -n` and helper compilation without execution pass. no numerical or broad command controls were repeated for this literal-only delta. this review read local source, git tree metadata and receipts only; no real/fixture artifact, analytical array, source pass, reader, evaluator, fit or composition was called. no production edit, launch or commit was made by this reviewer. fresh paths and the actual launch remain root's responsibility.
