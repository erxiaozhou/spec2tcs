(module
  (type (;0;) (func (param i32 i32 i32 i32) (result i32)))
  (type (;1;) (func (param i32)))
  (type (;2;) (func))
  ;; (global $one_v128_global_ v128 v128.const i8x16 1 2 3 4 5 6 7 8 9 10 0 255 15 240 13 12)
  ;; (global $one_v128_global2_ (mut v128) v128.const i32x4 254 1023 15 0)
  ;; (import "wasi_unstable" "fd_write" (func $wasi_fd_write (param i32 i32 i32 i32) (result i32)))
  ;; (import "wasi_unstable" "proc_exit" (func $wasi_proc_exit (param i32)))
  (global $one_i32_global_ i32 i32.const 541)
  (global $one_i32_global2_ (mut i32) i32.const 191)
  (global $one_f32_global_ f32 f32.const 541.0)
  (global $one_f32_global2_ (mut f32) f32.const 192.0)
  (global $one_i64_global_ i64 i64.const 54)
  (global $one_i64_global2_ (mut i64) i64.const 19)
  (global $one_f64_global_ f64 f64.const 54.0)
  (global $one_f64_global2_ (mut f64) f64.const 19.0)
  ;; store local
  (global  (mut i32) i32.const 0)
  (global  (mut f32) f32.const 0)
  (global  (mut i64) i64.const 0)
  (global  (mut f64) f64.const 0)
  (func 
    (local i32 f32 i64 f64)
    ;; (local i32 i64 f32 f64 v128)
    i32.const 305419896
    local.set 0
    f32.const 0x1.8cp+6 (;=99;)
    local.set 1
    i64.const -72057589709208571
    local.set 2
    f64.const 0x1.5f0b08c960a79p+109 (;=8.9e+32;)
    local.set 3
    ;; local for stack
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    local.get 0
    global.set 8
    local.get 1
    global.set 9
    local.get 2
    global.set 10
    local.get 3
    global.set 11
  )
  (func (result i32)
  i32.const  1
  i32.const  3
  i32.add
  )
  (func (result i32)
  i32.const  2
  i32.const  3
  i32.add
  )
  (func (result i32)
  i32.const  3
  i32.const  3
  i32.add
  )
  (memory (;0;) 1 5)
  ;; (export "memory" (memory 0))
  (export "_start" (func 0))
  (export "to_test" (func 0))
  (table (;0;) 10 20 funcref)
  (elem (;0;) (i32.const 0) func 1 2 3 0 1)
  (elem (;0;) (i32.const 5) funcref (ref.func 3) (ref.func 3) (ref.func 2) (ref.func 1))
  (elem (;0;) (i32.const 9) funcref (ref.func 0))
  (data (;0;) (i32.const 8) "\01\02\03\04\05\06\07\08")
  (data (;1;) (i32.const 16) "\01\02\03\04\05\06\07\08\ff")
  (data (;2;) (i32.const 32) "\01\02\03\04\05\06\07\08\ff"))