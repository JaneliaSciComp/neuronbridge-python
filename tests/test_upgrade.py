#!/usr/bin/env python
from neuronbridge.upgrade_model import *

if __name__ == '__main__':

    def convert(filename, convert_lambda):
        with open("test_data/"+filename) as f:
            obj = convert_lambda(json.load(f))
        with open("test_data_v3/"+filename, "w") as w:
            json.dump(obj.dict(exclude_unset=True, by_alias=True), w, indent=2)

    convert("em-body.json", lambda x: upgrade_em_lookup(legacy_model.EMImageLookup(**x)))
    convert("em-body-vnc.json", lambda x: upgrade_em_lookup(legacy_model.EMImageLookup(**x)))
    convert("mcfo-line.json", lambda x: upgrade_lm_lookup(legacy_model.LMImageLookup(**x)))
    convert("mcfo-line-vnc.json", lambda x: upgrade_lm_lookup(legacy_model.LMImageLookup(**x)))
    convert("flyem-flylight.json", lambda x: upgrade_cds_matches(legacy_model.CDSMatches(**x)))
    convert("flyem-flylight-vnc.json", lambda x: upgrade_cds_matches(legacy_model.CDSMatches(**x)))
    convert("flylight-flyem.json", lambda x: upgrade_cds_matches(legacy_model.CDSMatches(**x)))
    convert("flylight-flyem-vnc.json", lambda x: upgrade_cds_matches(legacy_model.CDSMatches(**x)))
    convert("pppresult.json", lambda x: upgrade_ppp_matches(legacy_model.PPPMatches(**x)))
    convert("pppresult-vnc.json", lambda x: upgrade_ppp_matches(legacy_model.PPPMatches(**x)))
