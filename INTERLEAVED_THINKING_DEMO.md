# Interleaved Thinking: Visual Demonstration

## What is Interleaved Thinking?

Traditional LLMs follow a linear pattern:
1. Think once upfront
2. Execute all tool calls in sequence
3. Return final answer

MiniMax-M2 uses **interleaved thinking**:
1. Think about task
2. Execute tool call
3. **Think about result** ← KEY DIFFERENCE
4. Decide next action based on what happened
5. Execute next tool call
6. Think again...
7. Repeat until task complete

This creates an adaptive agent that course-corrects based on real feedback.

## Why It Matters

### Example: Debugging a Web Application

**Linear Model (Claude, GPT-4):**
```
1. [THINK] Need to check logs, test API, inspect database
2. [TOOL] read_file("server.log")
3. [TOOL] run_command("curl http://localhost:3000/api/users")
4. [TOOL] run_command("psql -c 'SELECT * FROM users'")
5. [THINK] Based on all results, the issue is...
```

Problem: If step 2 reveals the actual issue, steps 3-4 are wasted.

**M2 with Interleaved Thinking:**
```
1. [THINK] Start by checking server logs for errors
2. [TOOL] read_file("server.log")
3. [THINK] Logs show database connection timeout. Check database status.
4. [TOOL] run_command("pg_isready")
5. [THINK] Database is down. Check if process is running.
6. [TOOL] run_command("ps aux | grep postgres")
7. [THINK] Process not found. Database crashed. Check startup script.
```

M2 adapts strategy after each result, avoiding unnecessary work.

## Visual Demonstration Concept

### Interactive Web Visualization

Build a web app that shows both execution patterns side-by-side with the same task.

```
+---------------------------+---------------------------+
|     Linear Model          |    M2 Interleaved         |
+---------------------------+---------------------------+
|  Thinking...              |  Thinking...              |
|  [Planning all steps]     |  [Planning first step]    |
|                           |                           |
|  Tool Call 1 →            |  Tool Call 1 →            |
|  Tool Call 2 →            |  ← Result                 |
|  Tool Call 3 →            |  Thinking...              |
|  Tool Call 4 →            |  [Adapting strategy]      |
|                           |                           |
|  ← All Results            |  Tool Call 2 →            |
|                           |  ← Result                 |
|  Thinking...              |  Thinking...              |
|  [Analyzing results]      |  [Success!]               |
+---------------------------+---------------------------+
```

## Implementation

### Project Structure

```
interleaved-thinking-demo/
├── backend/
│   ├── m2_executor.py         # Execute with M2
│   ├── claude_executor.py     # Execute with Claude
│   ├── task_scenarios.py      # Test scenarios
│   └── api.py                 # FastAPI server
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ThinkingBlock.tsx      # Show thinking process
│   │   │   ├── ToolCallBlock.tsx      # Show tool executions
│   │   │   ├── ComparisonView.tsx     # Side-by-side
│   │   │   └── FlowDiagram.tsx        # Graph visualization
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── scenarios/
    ├── debugging_task.json
    ├── api_building_task.json
    └── data_analysis_task.json
```

### Backend: Task Execution

```python
# backend/m2_executor.py

from openai import OpenAI
from typing import List, Dict
import json

class M2Executor:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.minimax.io/v1"
        )
    
    def execute_with_visualization(self, task: str, tools: List[Dict]) -> List[Dict]:
        """Execute task and capture full reasoning chain for visualization"""
        messages = [{"role": "user", "content": task}]
        execution_steps = []
        
        step_num = 0
        
        while True:
            step_num += 1
            
            # Call M2
            response = self.client.chat.completions.create(
                model="MiniMax-M2",
                messages=messages,
                tools=tools,
                extra_body={"reasoning_split": True}
            )
            
            message = response.choices[0].message
            
            # Capture thinking
            thinking = None
            if hasattr(message, 'reasoning_details') and message.reasoning_details:
                thinking = message.reasoning_details[0].get('text', '')
            
            execution_steps.append({
                'type': 'thinking',
                'step': step_num,
                'content': thinking,
                'timestamp': time.time()
            })
            
            # Preserve message in history
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": message.tool_calls,
                "reasoning_details": getattr(message, 'reasoning_details', None)
            })
            
            # If done, return
            if not message.tool_calls:
                execution_steps.append({
                    'type': 'completion',
                    'step': step_num,
                    'content': message.content,
                    'timestamp': time.time()
                })
                break
            
            # Execute tools
            for tool_call in message.tool_calls:
                execution_steps.append({
                    'type': 'tool_call',
                    'step': step_num,
                    'tool': tool_call.function.name,
                    'args': json.loads(tool_call.function.arguments),
                    'timestamp': time.time()
                })
                
                # Execute tool
                result = self._execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                
                execution_steps.append({
                    'type': 'tool_result',
                    'step': step_num,
                    'tool': tool_call.function.name,
                    'result': result,
                    'timestamp': time.time()
                })
                
                # Add result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        
        return execution_steps
    
    def _execute_tool(self, name: str, args: Dict) -> Any:
        # Tool implementations
        pass
```

### Frontend: Visualization Components

```tsx
// frontend/src/components/ComparisonView.tsx

import React, { useState, useEffect } from 'react';
import ThinkingBlock from './ThinkingBlock';
import ToolCallBlock from './ToolCallBlock';

interface ExecutionStep {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'completion';
  step: number;
  content?: string;
  tool?: string;
  args?: any;
  result?: any;
  timestamp: number;
}

export default function ComparisonView({ taskId }: { taskId: string }) {
  const [m2Steps, setM2Steps] = useState<ExecutionStep[]>([]);
  const [claudeSteps, setClaudeSteps] = useState<ExecutionStep[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  useEffect(() => {
    // Fetch execution data
    fetch(`/api/execute/${taskId}`)
      .then(r => r.json())
      .then(data => {
        setM2Steps(data.m2_steps);
        setClaudeSteps(data.claude_steps);
      });
  }, [taskId]);
  
  // Playback control
  useEffect(() => {
    if (!isPlaying) return;
    
    const timer = setTimeout(() => {
      setCurrentStep(prev => 
        prev < Math.max(m2Steps.length, claudeSteps.length) - 1 
          ? prev + 1 
          : prev
      );
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [isPlaying, currentStep, m2Steps, claudeSteps]);
  
  const m2Visible = m2Steps.slice(0, currentStep + 1);
  const claudeVisible = claudeSteps.slice(0, currentStep + 1);
  
  return (
    <div className="h-screen flex flex-col">
      {/* Control Bar */}
      <div className="bg-gray-800 text-white p-4 flex items-center gap-4">
        <h1 className="text-xl font-bold">Interleaved Thinking Demo</h1>
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="px-4 py-2 bg-blue-500 rounded"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button
          onClick={() => setCurrentStep(0)}
          className="px-4 py-2 bg-gray-600 rounded"
        >
          Reset
        </button>
        <div className="flex-1" />
        <span>Step {currentStep + 1} / {Math.max(m2Steps.length, claudeSteps.length)}</span>
      </div>
      
      {/* Split View */}
      <div className="flex-1 flex">
        {/* Claude Linear */}
        <div className="flex-1 border-r border-gray-300 overflow-y-auto p-6 bg-gray-50">
          <h2 className="text-2xl font-bold mb-4 text-gray-700">
            Linear Model (Claude)
          </h2>
          <div className="space-y-4">
            {claudeVisible.map((step, idx) => (
              <ExecutionStepComponent key={idx} step={step} />
            ))}
          </div>
        </div>
        
        {/* M2 Interleaved */}
        <div className="flex-1 overflow-y-auto p-6 bg-blue-50">
          <h2 className="text-2xl font-bold mb-4 text-blue-700">
            M2 Interleaved Thinking
          </h2>
          <div className="space-y-4">
            {m2Visible.map((step, idx) => (
              <ExecutionStepComponent 
                key={idx} 
                step={step} 
                highlight={step.type === 'thinking'}
              />
            ))}
          </div>
        </div>
      </div>
      
      {/* Stats Bar */}
      <div className="bg-white border-t border-gray-300 p-4 flex gap-8">
        <StatCard 
          label="Claude Tool Calls" 
          value={claudeSteps.filter(s => s.type === 'tool_call').length}
        />
        <StatCard 
          label="M2 Tool Calls" 
          value={m2Steps.filter(s => s.type === 'tool_call').length}
          highlight
        />
        <StatCard 
          label="M2 Thinking Episodes" 
          value={m2Steps.filter(s => s.type === 'thinking').length}
          highlight
        />
      </div>
    </div>
  );
}

function ExecutionStepComponent({ 
  step, 
  highlight 
}: { 
  step: ExecutionStep; 
  highlight?: boolean; 
}) {
  if (step.type === 'thinking') {
    return (
      <div className={`p-4 rounded-lg border-l-4 ${
        highlight ? 'bg-blue-100 border-blue-500' : 'bg-gray-100 border-gray-400'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">💭</span>
          <span className="font-semibold">Thinking</span>
        </div>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          {step.content?.substring(0, 300)}
          {step.content && step.content.length > 300 ? '...' : ''}
        </p>
      </div>
    );
  }
  
  if (step.type === 'tool_call') {
    return (
      <div className="p-4 bg-white rounded-lg border border-gray-300">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">🔧</span>
          <span className="font-semibold">Tool Call: {step.tool}</span>
        </div>
        <pre className="text-xs bg-gray-50 p-2 rounded">
          {JSON.stringify(step.args, null, 2)}
        </pre>
      </div>
    );
  }
  
  if (step.type === 'tool_result') {
    return (
      <div className="p-4 bg-green-50 rounded-lg border border-green-300">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">✅</span>
          <span className="font-semibold">Result: {step.tool}</span>
        </div>
        <pre className="text-xs bg-white p-2 rounded max-h-32 overflow-y-auto">
          {typeof step.result === 'string' 
            ? step.result.substring(0, 200)
            : JSON.stringify(step.result, null, 2).substring(0, 200)}
        </pre>
      </div>
    );
  }
  
  return null;
}

function StatCard({ 
  label, 
  value, 
  highlight 
}: { 
  label: string; 
  value: number; 
  highlight?: boolean; 
}) {
  return (
    <div className={`px-4 py-2 rounded ${
      highlight ? 'bg-blue-100' : 'bg-gray-100'
    }`}>
      <div className="text-sm text-gray-600">{label}</div>
      <div className={`text-2xl font-bold ${
        highlight ? 'text-blue-600' : 'text-gray-800'
      }`}>
        {value}
      </div>
    </div>
  );
}
```

## Demo Scenarios

### Scenario 1: API Development with Bug

**Task**: "Build a REST API for user management with authentication"

**What happens:**

**Claude (Linear):**
1. Thinks: Plan entire API structure
2. Tool: Write user model
3. Tool: Write auth middleware
4. Tool: Write routes
5. Tool: Write tests
6. Thinks: Review all code
7. Tool: Run tests
8. Result: Tests fail due to JWT secret missing

**M2 (Interleaved):**
1. Thinks: Start with user model
2. Tool: Write user model
3. Thinks: Model looks good, add auth
4. Tool: Write auth middleware
5. Thinks: Need JWT secret configured
6. Tool: Create .env with JWT_SECRET
7. Thinks: Now write routes using auth
8. Tool: Write routes
9. Thinks: Add tests
10. Tool: Write tests
11. Tool: Run tests
12. Thinks: All passing!

**Result**: M2 caught configuration issue early and handled proactively.

### Scenario 2: Data Analysis

**Task**: "Analyze sales data and create visualization"

**Claude:**
1. Thinks: Load data, clean, analyze, visualize
2. Tool: read_csv("sales.csv")
3. Tool: Clean data
4. Tool: Calculate metrics
5. Tool: Create chart
6. Thinks: Data has outliers affecting chart
7. Tool: Re-clean with outlier removal
8. Tool: Re-create chart

**M2:**
1. Thinks: First, examine data structure
2. Tool: read_csv("sales.csv")
3. Thinks: Large outliers present, need cleaning
4. Tool: Clean data with outlier removal
5. Thinks: Now calculate metrics
6. Tool: Calculate metrics
7. Thinks: Metrics look good, create chart
8. Tool: Create chart
9. Thinks: Chart clearly shows trends

**Result**: M2 identified data quality issue immediately after loading, avoided rework.

### Scenario 3: Complex Debugging

**Task**: "User login is broken, fix it"

**Claude:**
1. Thinks: Check frontend, backend, database
2. Tool: Read frontend code
3. Tool: Read backend code
4. Tool: Check database
5. Tool: Check logs
6. Thinks: Issue is in JWT validation
7. Tool: Fix JWT validation
8. Tool: Test

**M2:**
1. Thinks: Start with error logs
2. Tool: Read logs
3. Thinks: "JWT malformed" error, check JWT generation
4. Tool: Read auth service
5. Thinks: JWT secret is undefined, check env
6. Tool: Read .env
7. Thinks: JWT_SECRET missing, add it
8. Tool: Update .env
9. Tool: Restart server
10. Tool: Test login
11. Thinks: Fixed!

**Result**: M2 follows error trail efficiently, each tool call informed by previous result.

## Key Metrics to Highlight

### Efficiency Metrics
- **Tool Calls**: M2 often uses fewer tools by adapting strategy
- **Wasted Work**: M2 avoids redundant operations
- **Time to Solution**: Faster due to adaptive approach

### Quality Metrics
- **First-Try Success**: M2 catches issues earlier
- **Error Recovery**: M2 adapts when things fail
- **Solution Quality**: Similar or better outcomes

### Cost Metrics
- **Total Tokens**: M2 uses more thinking tokens but saves on redundant tool calls
- **Overall Cost**: Still 10x cheaper than Claude despite extra thinking

## Visualization Enhancements

### 1. Flow Graph

Show decision tree:
```
Start
  ↓
Think about approach
  ↓
Tool Call 1
  ↓
[Result indicates X] ← M2 analyzes here
  ↓
Think: Change strategy to Y
  ↓
Tool Call 2 (different from original plan)
  ↓
Success
```

Compare to linear:
```
Start
  ↓
Think about approach (plan all steps)
  ↓
Tool Call 1
  ↓
Tool Call 2
  ↓
Tool Call 3
  ↓
Tool Call 4
  ↓
[Analyze all results]
  ↓
Result
```

### 2. Adaptation Highlights

Highlight moments where M2 changed strategy:
- "Based on the log error, switching from checking frontend to checking environment variables"
- "Test failed, adapting approach to add missing validation"
- "API returned 401, need to check authentication first"

### 3. Efficiency Comparison

Show side-by-side:
- Number of thinking episodes
- Number of tool calls
- Number of adaptations
- Total time
- Total cost

## Expected Insights

After viewing the demo, users should understand:

1. **Interleaved thinking enables adaptation**: M2 doesn't commit to a plan, it adapts
2. **More efficient execution**: Fewer wasted tool calls
3. **Better error handling**: Course-corrects based on results
4. **Still cost-effective**: Extra thinking tokens are offset by efficiency
5. **Superior for complex tasks**: The longer the task, the more M2's approach shines

## Implementation Timeline

**Day 1**: Backend execution engine
- M2 executor with full reasoning capture
- Claude executor for comparison
- 3 demo scenarios

**Day 2**: Frontend visualization
- Split-view comparison
- Playback controls
- Styling

**Day 3**: Flow graph visualization
- D3.js decision tree
- Adaptation highlighting
- Metrics display

**Day 4**: Polish and demo video
- Record demo videos
- Write explanatory content
- Prepare for presentation

## Demo Script

**Opening**: "Traditional AI models plan everything upfront. MiniMax-M2 thinks between each action."

**Show**: Side-by-side execution of debugging task

**Highlight**: "Notice how M2 adapts strategy after seeing the log error, while Claude continues with its original plan."

**Result**: "M2 solved it in 8 steps, Claude needed 11 and had to backtrack."

**Cost**: "M2: $0.08, Claude: $1.20 - that's 15x cheaper for better results."

**Close**: "Interleaved thinking isn't just a feature, it's how humans solve problems. M2 brings that to AI."

