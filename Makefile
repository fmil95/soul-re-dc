# Soul Reaver (Dreamcast) matching decompilation.
# Run from WSL/Linux with wine installed:  make setup && make
#
#   make setup   - extract 1ST_READ.BIN from the GDI and install the SDK toolchain for wine
#   make         - split, build build/1ST_READ.BIN and compare against the original

PYTHON   ?= python3
# Path to the .gdi; if unset, the first *.gdi in the repo root is used (the name may contain spaces).
GDI      ?=
DCTOOL   := bash tools/dctool.sh
NAME     := 1st_read
TARGET   := build/1ST_READ.BIN
CONFIG   := config/$(NAME).toml

CC1FLAGS := -quiet -ml -m4-single-only -O2 -fno-delayed-branch
ASFLAGS  := -little

.PHONY: all setup split compare clean psx-match gen-c
all: compare

setup:
	@gdi='$(GDI)'; \
	if [ -z "$$gdi" ]; then set -- *.gdi; gdi="$$1"; fi; \
	if [ ! -f "$$gdi" ]; then echo "error: no .gdi found in $$(pwd) (or pass GDI=path)" >&2; exit 1; fi; \
	echo "$(PYTHON) tools/extract_gdi.py \"$$gdi\" rom"; \
	$(PYTHON) tools/extract_gdi.py "$$gdi" rom
	bash tools/setup_toolchain.sh

split: build/$(NAME).ld

# Also generates asm/nonmatchings/**.s from config/functions.csv.
build/$(NAME).ld build/$(NAME).objs: $(CONFIG) config/functions.csv tools/split.py tools/gen_asm.py rom/1ST_READ.BIN
	$(PYTHON) tools/split.py $(CONFIG)

# Create src/**/*.c (INCLUDE_ASM stubs) for files in config/functions.csv that don't exist yet.
gen-c:
	$(PYTHON) tools/gen_c.py

.SECONDEXPANSION:
build/src/%.o: src/%.c $$(wildcard asm/nonmatchings/$$*/*.s) include/common.h | build/$(NAME).ld
	@mkdir -p $(dir $@)
	$(DCTOOL) cpp -lang-c -D__sh__ -D__ELF__ -D__LITTLE_ENDIAN__ -D__SH4_SINGLE_ONLY__ -D__OPTIMIZE__ -Iinclude $< build/src/$*.i
	$(DCTOOL) cc1 build/src/$*.i $(CC1FLAGS) -o build/src/$*.s
	$(DCTOOL) as $(ASFLAGS) -o $@ build/src/$*.s

build/asm/%.o: asm/%.s
	@mkdir -p $(dir $@)
	$(DCTOOL) as $(ASFLAGS) -o $@ $<

# Objects are listed by the splitter; re-read after it runs.
-include build/$(NAME).deps
build/$(NAME).deps: build/$(NAME).objs
	@echo "OBJS := $$(tr '\n' ' ' < $<)" > $@

build/$(NAME).elf: build/$(NAME).ld $(OBJS)
	$(DCTOOL) ld -m shlelf -T build/$(NAME).ld -o $@ $(OBJS) -Map build/$(NAME).map

$(TARGET): build/$(NAME).elf
	$(DCTOOL) objcopy -O binary $< $@

compare: $(TARGET)
	@$(PYTHON) tools/compare.py $(CONFIG) $(TARGET)

# Cross-reference with the PSX decomp (needs a built soul-re checkout: build/*.elf and build/*.map).
PSX ?= $(HOME)/soul-re
psx-match:
	$(PYTHON) tools/psx_match.py --psx "$(PSX)" --out config

clean:
	rm -rf build
