#!/usr/bin/env python3
"""
示例数据库创建脚本

Sample Database Creation Script for Testing
"""

import asyncio
import sqlite3
import json
import sys
from pathlib import Path

# 添加父目录到路径以支持导入
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from tools.database_tools import SQLiteConnector, db_tool_manager
except ImportError:
    from database_tools import SQLiteConnector, db_tool_manager


async def create_sample_database(db_path: str = "sample_verilog.db"):
    """创建示例数据库"""
    
    # 确保目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 创建连接
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    try:
        # 创建verilog_modules表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verilog_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                functionality TEXT,
                bit_width INTEGER,
                tags TEXT,
                code TEXT,
                quality_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # 创建test_cases表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER,
                module_name TEXT,
                test_type TEXT,
                test_vectors TEXT,
                expected_results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (module_id) REFERENCES verilog_modules (id)
            )
        """)
        
        # 创建design_patterns表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS design_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                code_template TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 插入示例数据
        sample_modules = [
            # ALU模块
            (
                "alu_32bit", "32位算术逻辑单元",
                "arithmetic_logic", 32, "alu,arithmetic,logic",
                """module alu_32bit (
    input wire [31:0] a, b,
    input wire [3:0] op,
    output reg [31:0] result,
    output wire zero, overflow
);
    always @(*) begin
        case (op)
            4'b0000: result = a + b;    // ADD
            4'b0001: result = a - b;    // SUB
            4'b0010: result = a & b;    // AND
            4'b0011: result = a | b;    // OR
            4'b0100: result = a ^ b;    // XOR
            4'b0101: result = ~a;       // NOT
            4'b0110: result = a << b[4:0]; // SHL
            4'b0111: result = a >> b[4:0]; // SHR
            default: result = 32'b0;
        endcase
    end
    assign zero = (result == 0);
    assign overflow = 1'b0; // Simplified
endmodule""",
                0.95, 15
            ),
            
            # 计数器模块
            (
                "counter_8bit", "8位二进制计数器",
                "counter", 8, "counter,sequential,binary",
                """module counter_8bit (
    input wire clk, rst_n, enable,
    input wire up_down, // 1: up, 0: down
    output reg [7:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'b0;
        else if (enable) begin
            if (up_down)
                count <= count + 1;
            else
                count <= count - 1;
        end
    end
endmodule""",
                0.90, 8
            ),
            
            # FIFO模块
            (
                "fifo_16x8", "16深度8位FIFO缓冲器",
                "fifo", 8, "fifo,buffer,memory",
                """module fifo_16x8 (
    input wire clk, rst_n,
    input wire wr_en, rd_en,
    input wire [7:0] data_in,
    output reg [7:0] data_out,
    output wire full, empty
);
    reg [7:0] memory [0:15];
    reg [4:0] wr_ptr, rd_ptr;
    reg [4:0] count;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count <= 0;
        end else begin
            if (wr_en && !full) begin
                memory[wr_ptr[3:0]] <= data_in;
                wr_ptr <= wr_ptr + 1;
                count <= count + 1;
            end
            if (rd_en && !empty) begin
                data_out <= memory[rd_ptr[3:0]];
                rd_ptr <= rd_ptr + 1;
                count <= count - 1;
            end
        end
    end
    
    assign full = (count == 16);
    assign empty = (count == 0);
endmodule""",
                0.88, 5
            ),
            
            # 加法器模块
            (
                "adder_16bit", "16位加法器",
                "adder", 16, "adder,arithmetic,combinational",
                """module adder_16bit (
    input wire [15:0] a, b,
    input wire cin,
    output wire [15:0] sum,
    output wire cout
);
    assign {cout, sum} = a + b + cin;
endmodule""",
                0.85, 12
            ),
            
            # 乘法器模块
            (
                "multiplier_8bit", "8位乘法器",
                "multiplier", 8, "multiplier,arithmetic,sequential",
                """module multiplier_8bit (
    input wire clk, rst_n, start,
    input wire [7:0] a, b,
    output reg [15:0] product,
    output reg done
);
    reg [7:0] multiplicand, multiplier;
    reg [15:0] partial_product;
    reg [3:0] count;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            product <= 0;
            done <= 0;
            count <= 0;
        end else if (start && !done) begin
            if (count == 0) begin
                multiplicand <= a;
                multiplier <= b;
                partial_product <= 0;
            end
            
            if (multiplier[0])
                partial_product <= partial_product + (multiplicand << count);
            
            multiplier <= multiplier >> 1;
            count <= count + 1;
            
            if (count == 7) begin
                product <= partial_product;
                done <= 1;
            end
        end else if (!start) begin
            done <= 0;
            count <= 0;
        end
    end
endmodule""",
                0.82, 3
            )
        ]
        
        # 插入模块数据
        cursor.executemany("""
            INSERT INTO verilog_modules 
            (name, description, functionality, bit_width, tags, code, quality_score, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_modules)
        
        # 插入测试用例
        sample_test_cases = [
            (1, "alu_32bit", "functional", 
             '[{"a": "32\'h12345678", "b": "32\'h87654321", "op": "4\'b0000"}]',
             '[{"result": "32\'h99999999", "zero": "1\'b0"}]'),
            (1, "alu_32bit", "boundary",
             '[{"a": "32\'hFFFFFFFF", "b": "32\'h00000001", "op": "4\'b0000"}]',
             '[{"result": "32\'h00000000", "zero": "1\'b1"}]'),
            (2, "counter_8bit", "functional",
             '[{"enable": "1\'b1", "up_down": "1\'b1"}]',
             '[{"count": "8\'h01"}, {"count": "8\'h02"}, {"count": "8\'h03"}]'),
            (3, "fifo_16x8", "functional",
             '[{"wr_en": "1\'b1", "data_in": "8\'hAA"}]',
             '[{"full": "1\'b0", "empty": "1\'b0"}]')
        ]
        
        cursor.executemany("""
            INSERT INTO test_cases (module_id, module_name, test_type, test_vectors, expected_results)
            VALUES (?, ?, ?, ?, ?)
        """, sample_test_cases)
        
        # 插入设计模式
        sample_patterns = [
            ("fsm", "Moore状态机", "Moore型有限状态机设计模式",
             """// Moore FSM Template
module moore_fsm (
    input wire clk, rst_n,
    input wire [INPUT_WIDTH-1:0] inputs,
    output reg [OUTPUT_WIDTH-1:0] outputs
);
    // State definitions
    typedef enum logic [STATE_BITS-1:0] {
        STATE_IDLE,
        STATE_ACTIVE,
        STATE_DONE
    } state_t;
    
    state_t current_state, next_state;
    
    // State register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= STATE_IDLE;
        else
            current_state <= next_state;
    end
    
    // Next state logic
    always @(*) begin
        case (current_state)
            STATE_IDLE: next_state = inputs ? STATE_ACTIVE : STATE_IDLE;
            STATE_ACTIVE: next_state = inputs ? STATE_DONE : STATE_IDLE;
            STATE_DONE: next_state = STATE_IDLE;
            default: next_state = STATE_IDLE;
        endcase
    end
    
    // Output logic (Moore)
    always @(*) begin
        case (current_state)
            STATE_IDLE: outputs = OUTPUT_IDLE_VALUE;
            STATE_ACTIVE: outputs = OUTPUT_ACTIVE_VALUE;
            STATE_DONE: outputs = OUTPUT_DONE_VALUE;
            default: outputs = OUTPUT_DEFAULT_VALUE;
        endcase
    end
endmodule""", 25),
            
            ("pipeline", "流水线设计", "多阶段流水线设计模式",
             """// Pipeline Template
module pipeline_stage #(
    parameter DATA_WIDTH = 32,
    parameter STAGE_NUM = 1
) (
    input wire clk, rst_n,
    input wire [DATA_WIDTH-1:0] data_in,
    input wire valid_in,
    output reg [DATA_WIDTH-1:0] data_out,
    output reg valid_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= 0;
            valid_out <= 0;
        end else begin
            data_out <= data_in;  // Process data here
            valid_out <= valid_in;
        end
    end
endmodule""", 15),
            
            ("clock_domain", "时钟域crossing", "跨时钟域数据传输设计模式",
             """// Clock Domain Crossing Template
module cdc_synchronizer #(
    parameter DATA_WIDTH = 1,
    parameter SYNC_STAGES = 2
) (
    input wire src_clk, dst_clk,
    input wire rst_n,
    input wire [DATA_WIDTH-1:0] src_data,
    output reg [DATA_WIDTH-1:0] dst_data
);
    reg [DATA_WIDTH-1:0] sync_regs [0:SYNC_STAGES-1];
    
    always @(posedge dst_clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < SYNC_STAGES; i++)
                sync_regs[i] <= 0;
        end else begin
            sync_regs[0] <= src_data;
            for (int i = 1; i < SYNC_STAGES; i++)
                sync_regs[i] <= sync_regs[i-1];
        end
    end
    
    assign dst_data = sync_regs[SYNC_STAGES-1];
endmodule""", 8)
        ]
        
        cursor.executemany("""
            INSERT INTO design_patterns (pattern_type, name, description, code_template, usage_count)
            VALUES (?, ?, ?, ?, ?)
        """, sample_patterns)
        
        connection.commit()
        print(f"✅ 示例数据库创建成功: {db_path}")
        print(f"   - 模块数量: {len(sample_modules)}")
        print(f"   - 测试用例: {len(sample_test_cases)}")
        print(f"   - 设计模式: {len(sample_patterns)}")
        
        return db_path
        
    except Exception as e:
        print(f"❌ 创建示例数据库失败: {str(e)}")
        raise
    finally:
        connection.close()


async def setup_database_for_framework(db_path: str = "sample_verilog.db"):
    """为框架设置数据库"""
    # 创建示例数据库
    await create_sample_database(db_path)
    
    # 配置数据库连接器
    connector = SQLiteConnector({"db_path": db_path})
    
    # 注册到工具管理器
    db_tool_manager.register_connector("default", connector, is_default=True)
    
    # 连接数据库
    await db_tool_manager.connect_all()
    
    print(f"🗄️ 数据库工具管理器配置完成")
    return connector


if __name__ == "__main__":
    # 直接运行此脚本创建示例数据库
    asyncio.run(create_sample_database())