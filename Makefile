# Soul Reaver (Dreamcast) matching decompilation.
# Run from WSL/Linux with wine installed:  make setup && make
#
#   make setup   - extract 1ST_READ.BIN from the GDI and install the SDK toolchain for wine
#   make         - split, build build/1ST_READ.BIN and compare against the original

PYTHON   ?= python3
GDI      ?= $(firstword $(wildcard *.gdi))
DCTOOL   := bash tools/dctool.sh
NAME     := 1st_read
TARGET   := build/1ST_READ.BIN
CONFIG   := config/$(NAME).toml

CC1FLAGS := -quiet -ml -m4-single-only -O2
ASFLAGS  := -little

.PHONY: all setup split compare clean
all: compare

setup:
	$(PYTHON) tools/extract_gdi.py "$(GDI)" rom
	bash tools/setup_toolchain.sh

split: build/$(NAME).ld

build/$(NAME).ld build/$(NAME).objs: $(CONFIG) tools/split.py rom/1ST_READ.BIN
	$(PYTHON) tools/split.py $(CONFIG)

build/src/%.o: src/%.c
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

clean:
	rm -rf build
