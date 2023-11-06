# (c) 2022-Present IObundle, Lda, all rights reserved
#
# This makefile simulates the hardware modules in this repo
#

LIB_DIR:=.
PROJECT_ROOT=..
DISABLE_LINT:=1
DISABLE_FORMAT:=1
# Default lib module to setup. Can be overriden by the user.
CORE ?=iob_ctls

all: sim-test

include setup.mk

sim-build:
	nix-shell --run "scripts/test.sh build $(CORE)"

sim-run:
	nix-shell --run "VCD=$(VCD) scripts/test.sh $(CORE)"

sim-test:
	nix-shell --run "scripts/test.sh test"

sim-clean:
	nix-shell --run "scripts/test.sh clean"


.PHONY: all sim-build sim-run sim-test sim-clean
