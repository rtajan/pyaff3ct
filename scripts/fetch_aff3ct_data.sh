#!/usr/bin/env bash
# AFF3CT data used by the tests and the documentation: the BER/FER reference curves (refs submodule, 5 MB) and, from
# the configuration files (a large repository), only the LDPC matrices used by the tests and the examples.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

git submodule update --init lib/aff3ct
git -C lib/aff3ct submodule update --init refs
CONF_SHA=$(git -C lib/aff3ct ls-tree HEAD conf | awk '{print $3}')
rm -rf lib/aff3ct/conf
git clone -q --filter=blob:none --no-checkout https://github.com/aff3ct/configuration_files.git lib/aff3ct/conf
git -C lib/aff3ct/conf sparse-checkout set --no-cone /dec/LDPC/CCSDS_64_128.alist /dec/LDPC/WIMAX_288_576.alist \
  /dec/LDPC/MACKAY_504_1008.alist /dec/LDPC/PEG_Reg_1008x504.alist \
  /cde/awgn_polar_codes/MK/ /cde/awgn_polar_codes/PT/7/ /mod/SCMA/ \
  /chn/optical_channel.dist /dec/LDPC/PureIRA_R_4_5_N16k_H.alist /dec/LDPC/PureIRA_R_9_10_N16k_H.alist
git -C lib/aff3ct/conf checkout -q "$CONF_SHA"
