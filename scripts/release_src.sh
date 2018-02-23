#! /bin/bash

#
# 1. change version number
# 2. Execute from soundgrain folder : ./scripts/release_src.sh
#

version=6.0.1
replace=XXX

src_rep=SoundGrain_XXX-src
src_tar=SoundGrain_XXX-src.tar.bz2

git checkout-index -a -f --prefix=${src_rep/$replace/$version}/
tar -cjvf ${src_tar/$replace/$version} ${src_rep/$replace/$version}
rm -R ${src_rep/$replace/$version}

