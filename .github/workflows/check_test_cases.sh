#!/bin/sh

echo "::group::Compile"
echo "Inside group"
source ./.github/workflows/macos_install.sh $HOME/install || true
# source ./.github/workflows/macos_install.sh $HOME/install || echo "::endgroup::" && exit 125
echo "::endgroup::"

echo "::group::Test"
export PYTHONPATH=$(grass --config python_path):$PYTHONPATH
export LD_LIBRARY_PATH=$(grass --config path)/lib:$LD_LIBRARY_PATH
pytest --verbose --color=yes --durations=0 --durations-min=0.5 \
            -ra . \
            -m 'needs_solo_run'
echo "::endgroup::"