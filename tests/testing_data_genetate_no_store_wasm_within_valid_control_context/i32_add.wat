(module
   (type (func (param i64) (result i32)))
   (type (func (param i32 f32) (result i32)))
   (type (func (result i32)))
  (func (result i32)
    i64.const 0 
    block (param i64) (result i32)
      drop
      i32.const 0
      f32.const 0
      block (param i32 f32) (result i32)
        drop
        drop
        i32.const 0
        i32.const 1
        i32.add
      end
    end
  )
  (export "_start" (func 0))
  (export "to_test" (func 0))
)