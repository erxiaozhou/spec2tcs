(module
   (type (func (param i32 i64 f32 v128) (result funcref externref)))
   (type (func (param i32 funcref externref) (result i32 i64 f32 f64 v128)))
   (type (func (result i32)))
  (func (result i32)
    i32.const 0
    i64.const 0
    f32.const 0
    v128.const i32x4 0 0 0 0
    block (param i32 i64 f32 v128) (result funcref externref)
      drop
      drop
      drop
      ref.null func
      ref.null extern
      block (param i32 funcref externref) (result i32 i64 f32 f64 v128)
        drop
        drop
        drop
        nop
        i32.const 0
        i64.const 0
        f32.const 0
        f64.const 0
        v128.const i32x4 0 0 0 0
      end
      drop
      drop
      drop
      drop
      drop
      ref.null func
      ref.null extern
    end
    drop
    drop
    i32.const 0
  )
  (export "_start" (func 0))
  (export "to_test" (func 0))
)