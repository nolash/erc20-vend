SOLC = /usr/bin/solc

all:
	$(SOLC) --bin Vend.sol --evm-version byzantium | awk 'NR>7' > Vend.bin
	$(SOLC) --abi Vend.sol --evm-version byzantium | awk 'NR>7' > Vend.json
	$(SOLC) --metadata Vend.sol --evm-version byzantium | awk 'NR>7' > Vend.metadata.json
	truncate -s -1 Vend.bin

install: all
	cp -v *.json ../python/erc20_vend/data/
	cp -v *.bin ../python/erc20_vend/data/

