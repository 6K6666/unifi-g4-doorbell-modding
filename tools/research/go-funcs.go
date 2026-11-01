// List functions in a stripped Go binary (such as the doorbell's ubnt_mcu) whose names contain a filter string.
// Usage: go run tools/research/go-funcs.go BINARY FILTER      e.g.  go run tools/research/go-funcs.go ubnt_mcu ipc.LED
// Go keeps every function name in its runtime table (.gopclntab) even when the symbol table is stripped.
package main

import (
	"debug/elf"
	"debug/gosym"
	"fmt"
	"os"
	"strings"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Println("usage: go run go-funcs.go BINARY FILTER")
		os.Exit(2)
	}
	f, err := elf.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	text, pcln := f.Section(".text"), f.Section(".gopclntab")
	if text == nil || pcln == nil {
		fmt.Println("no .text or .gopclntab section: not a Go binary, or one with its tables removed")
		os.Exit(1)
	}
	data, _ := pcln.Data()
	table, err := gosym.NewTable(nil, gosym.NewLineTable(data, text.Addr))
	if err != nil {
		panic(err)
	}
	for _, fn := range table.Funcs {
		if strings.Contains(fn.Name, os.Args[2]) {
			fmt.Printf("%#x-%#x %s\n", fn.Entry, fn.End, fn.Name)
		}
	}
}
