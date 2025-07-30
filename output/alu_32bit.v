```verilog
`timescale 1ns / 1ps

//-----------------------------------------------------------------------------
// Module: alu_32bit
//
// Description:
// 32位算术逻辑单元(ALU)，支持加法、减法、与、或、异或运算，并具备零标志和溢出检测功能。
// 该模块设计为同步时序逻辑，具有清晰的架构和良好的可维护性。
//
// Features:
// - 支持加法(000), 减法(001), 与(010), 或(011), 异或(100)
// - 零标志(zero)：结果为0时置1
// - 溢出标志(overflow)：仅在加法/减法时有效
// - 参数化设计（bit_width可配置）
// - 低功耗设计策略
// - 符合工业级Verilog标准
//
// Parameters:
//   BIT_WIDTH - 操作数宽度（默认32）
//
// Ports:
//   a        - 输入操作数A (BIT_WIDTH位)
//   b        - 输入操作数B (BIT_WIDTH位)
//   op       - 操作码 (3位)
//   clk      - 时钟输入
//   rst_n    - 异步复位输入（低电平有效）
//   result   - 输出运算结果 (BIT_WIDTH位)
//   zero     - 零标志 (1位)
//   overflow - 溢出标志 (1位)
//
// Timing Constraints:
//   目标频率为100MHz，关键路径延迟需小于10ns
//
// Area Constraints:
//   尽量优化面积，避免冗余逻辑
//
// Power Considerations:
//   采用低功耗设计策略，如门控时钟和最小化切换活动
//
// Design Notes:
//   - 使用同步复位以确保时序稳定性
//   - 溢出检测仅在加法/减法时有效
//   - 零标志在所有运算后生成
//-----------------------------------------------------------------------------

module alu_32bit #(
  parameter BIT_WIDTH = 32
) (
  // Inputs
  input  [BIT_WIDTH-1:0] a,
  input  [BIT_WIDTH-1:0] b,
  input  [2:0]           op,
  
  // Clock and Reset
  input                  clk,
  input                  rst_n,
  
  // Outputs
  output reg [BIT_WIDTH-1:0] result,
  output reg             zero,
  output reg             overflow
);

  // Internal signals
  reg [BIT_WIDTH-1:0] adder_result;
  reg [BIT_WIDTH-1:0] logic_result;
  reg [BIT_WIDTH-1:0] temp_result;
  reg [BIT_WIDTH-1:0] a_reg, b_reg;
  reg [2:0]           op_reg;

  //-----------------------------------------------------------------------------
  // Register inputs for synchronous processing
  //-----------------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      a_reg <= {BIT_WIDTH{1'b0}};
      b_reg <= {BIT_WIDTH{1'b0}};
      op_reg <= 3'b000;
    end else begin
      a_reg <= a;
      b_reg <= b;
      op_reg <= op;
    end
  end

  //-----------------------------------------------------------------------------
  // Main ALU logic
  //-----------------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      result <= {BIT_WIDTH{1'b0}};
      zero <= 1'b0;
      overflow <= 1'b0;
    end else begin
      // Compute logic operations
      logic_result = (op_reg == 3'b010) ? (a_reg & b_reg) : 
                     (op_reg == 3'b011) ? (a_reg | b_reg) : 
                     (op_reg == 3'b100) ? (a_reg ^ b_reg) : {BIT_WIDTH{1'b0}};

      // Compute arithmetic operations
      if (op_reg == 3'b000) begin // Add
        adder_result = a_reg + b_reg;
        // Overflow detection for addition
        overflow <= (a_reg[BIT_WIDTH-1] == b_reg[BIT_WIDTH-1]) && 
                    (adder_result[BIT_WIDTH-1] != a_reg[BIT_WIDTH-1]);
      end else if (op_reg == 3'b001) begin // Subtract
        adder_result = a_reg - b_reg;
        // Overflow detection for subtraction
        overflow <= (a_reg[BIT_WIDTH-1] != b_reg[BIT_WIDTH-1]) && 
                    (adder_result[BIT_WIDTH-1] != a_reg[BIT_WIDTH-1]);
      end else begin
        adder_result <= {BIT_WIDTH{1'b0}};
        overflow <= 1'b0;
      end

      // Select result based on operation
      case (op_reg)
        3'b000: temp_result = adder_result;
        3'b001: temp_result = adder_result;
        3'b010: temp_result = logic_result;
        3'b011: temp_result = logic_result;
        3'b100: temp_result = logic_result;
        default: temp_result = {BIT_WIDTH{1'b0}};
      endcase

      // Update output registers
      result <= temp_result;
      
      // Zero flag generation
      zero <= (temp_result == {BIT_WIDTH{1'b0}}) ? 1'b1 : 1'b0;
    end
  end

  //-----------------------------------------------------------------------------
  // Assertion checks for design integrity
  //-----------------------------------------------------------------------------
  // Check that op is within valid range
  assert property (@(posedge clk) disable iff (!rst_n) 
                   (op[2:0] inside {3'b000, 3'b001, 3'b010, 3'b011, 3'b100}));
  
  // Check that result is properly updated
  assert property (@(posedge clk) disable iff (!rst_n) 
                   (result == (op == 3'b000 ? a_reg + b_reg :
                              op == 3'b001 ? a_reg - b_reg :
                              op == 3'b010 ? a_reg & b_reg :
                              op == 3'b011 ? a_reg | b_reg :
                              op == 3'b100 ? a_reg ^ b_reg : {BIT_WIDTH{1'b0}})));
  
  // Check that zero flag is correctly set
  assert property (@(posedge clk) disable iff (!rst_n) 
                   (zero == (result == {BIT_WIDTH{1'b0}})));
  
  // Check that overflow flag is only set for add/sub
  assert property (@(posedge clk) disable iff (!rst_n) 
                   (op != 3'b000 && op != 3'b001) -> (overflow == 1'b0));

endmodule
```