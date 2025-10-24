# Transaction Tree Visualization Guide 🌳

## Overview

The **Transaction Tree** is a Git-like visualization that shows how transactions branch out, run concurrently, and merge back together - similar to how GitHub displays commit graphs!

## 🎯 What It Shows

```
Main Timeline (horizontal gray line)
    │
    ├─── TXN #1 (branches out) ──→ Commits (merges back) ✓
    │
    ├─── TXN #2 (branches out) ──→ Commits (merges back) ✓
    │    │
    │    └─── TXN #3 (concurrent) ──→ Aborts (red) ✗
    │
    └─── TXN #4 (branches out) ──→ Still Active...
```

## 🚀 Quick Start

### Step 1: Start Backend & Frontend

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Step 2: Open Browser

Open `http://localhost:5173` and click on the **"Transaction Tree"** tab

### Step 3: Create Transactions

In the Query Editor tab:
1. Click "Begin TXN" → Watch a new branch appear! 🌿
2. Execute some queries
3. Click "Commit" → Watch it merge back! 🔀

## 📊 Visual Elements

### Node Types

**🔵 Blue Circle** = Active Transaction (currently running)
- Has a filled blue center
- Transaction is in progress
- Not yet committed or aborted

**🟢 Green Circle** = Committed Transaction
- Successfully completed
- Changes are permanent
- Merged back to main line

**🔴 Red Circle** = Aborted Transaction
- Rolled back
- Changes discarded
- Marked as failed

### Connection Lines

**Curved Line Branching Out** (from main timeline)
- Transaction starts (BEGIN)
- Branches from the main flow
- Blue arrow indicates direction

**Curved Line Merging Back** (to main timeline)
- Transaction commits (green arrow)
- Or transaction aborts (red arrow)
- Rejoins the main flow

**Straight Line** (between nodes)
- Continuation on same lane
- Transaction progressing

## 🎨 Reading the Tree

### Example 1: Sequential Transactions

```
Main ──●──●──●──●──
      #1  #2  #3  #4

All transactions complete one after another
Simple linear flow
```

### Example 2: Concurrent Transactions

```
Main ──●─────────●──
       │         │
       ├─●───✓  │   TXN #2 commits
       │         │
       └────●────✗   TXN #3 aborts
       
TXN #2 and #3 run simultaneously
Then complete at different times
```

### Example 3: Complex Branching

```
Main ──●───────────●─────●──
       │           │
       ├─●──✓     │        TXN #2 (quick commit)
       │           │
       ├─●─────✓  │        TXN #3 (longer transaction)
       │           │
       └────●──────✗        TXN #4 (aborted)

Multiple concurrent transactions
Different durations
Mixed outcomes
```

## 🔍 Understanding Patterns

### Pattern 1: High Concurrency
```
Lots of branches = Many concurrent transactions
Good for throughput, watch for conflicts!
```

### Pattern 2: Sequential Processing
```
Single line = One transaction at a time
Safer but slower
```

### Pattern 3: Mixed Mode
```
Some branches, some sequential = Balanced approach
Typical of real applications
```

## 💡 Use Cases

### 1. Debugging Concurrency Issues

```
Problem: Transaction conflicts
Solution: Look at the tree to see which transactions overlap

If you see:
Main ──●───────────●──
       ├─●────✗    │     TXN #2 aborted
       └────●──────✓     TXN #3 committed

→ TXN #2 and #3 were concurrent
→ Check if they accessed same data
→ TXN #2 might have conflicted
```

### 2. Performance Analysis

```
Wide tree = High concurrency (good!)
Main ──●─────────────●──
       ├─●──✓
       ├─●──✓
       ├─●──✓
       └─●──✓

Tall tree = Long-running transactions (investigate!)
Main ──●─────────────────────────●──
       └─────────────────────────✓
       (Very long branch)
```

### 3. Learning MVCC

```
Perfect for teaching:
- How multiple transactions run simultaneously
- How MVCC allows non-blocking reads
- Visual representation of isolation
```

## 🎓 Step-by-Step Tutorial

### Tutorial 1: Your First Transaction

1. **Start a transaction**
   - Click "Begin TXN" in Query Editor
   - Watch: A blue circle appears, branching from the main line

2. **Execute a query**
   - Type: `CREATE TABLE test (id INT)`
   - Click "Execute Query"
   - Watch: Circle stays blue (still active)

3. **Commit the transaction**
   - Click "Commit"
   - Watch: Circle turns green, line merges back!

### Tutorial 2: Concurrent Transactions

1. **Open 2 browser tabs**
   - Tab 1: Transaction Tree (monitoring)
   - Tab 2: Query Editor (actions)

2. **In Tab 2: Start first transaction**
   - Click "Begin TXN"
   - Switch to Tab 1: See first branch

3. **In Tab 2: Start second transaction**
   - Click "Begin TXN" again
   - Switch to Tab 1: See second branch appear!

4. **Complete transactions**
   - Commit one, rollback the other
   - Watch them merge back with different colors

### Tutorial 3: Understanding Isolation Levels

1. **Create transaction with READ_UNCOMMITTED**
   - Notice how it appears on the tree
   - Label shows isolation level

2. **Create transaction with SERIALIZABLE**
   - Compare the branches
   - Both show on tree with their isolation levels

3. **Observe the differences**
   - Tree shows them visually separated
   - Easy to see which transactions might conflict

## 🎯 Interactive Features

### Hover Information (Future Enhancement)
- Hover over a node → See transaction details
- Hover over a line → See duration
- Click a node → Filter related queries

### Zoom & Pan (Future Enhancement)
- Scroll to zoom in/out
- Drag to pan around
- Useful for many transactions

### Filter Options (Future Enhancement)
- Show only active transactions
- Show only specific isolation level
- Time range filtering

## 📱 Multi-Tab Experience

### Tab 1: Query Editor
```
┌─────────────────┐
│ BEGIN TXN       │ ← Click this
│ INSERT ...      │
│ COMMIT          │
└─────────────────┘
```

### Tab 2: Transaction Tree
```
┌─────────────────┐
│   ●───●───●     │ ← Watch this update!
│   └─✓ └─✓       │
└─────────────────┘
```

Both tabs update in **real-time** via WebSocket!

## 🎨 Customization

### Colors

Currently:
- 🔵 Blue = Active (#3b82f6)
- 🟢 Green = Committed (#10b981)
- 🔴 Red = Aborted (#ef4444)

To customize, edit `frontend/src/components/TransactionTree.jsx`:
```javascript
const getNodeColor = (state) => {
  switch (state) {
    case 'ACTIVE': return '#your-color';
    // ...
  }
}
```

### Layout

Adjust spacing in the code:
```javascript
const nodeSpacing = 80;  // Horizontal spacing
const laneSpacing = 60;  // Vertical spacing
```

## 🐛 Troubleshooting

### Problem: Tree not updating

**Check:**
1. WebSocket connection (green "Live" indicator)
2. Backend running on port 8000
3. Browser console for errors

**Solution:**
- Refresh page
- Check backend logs
- Ensure ports aren't blocked

### Problem: Lines overlap

**Explanation:**
- Expected with many concurrent transactions
- Shows high concurrency (good thing!)

**If too cluttered:**
- Filter transactions
- Or use Transactions tab for list view

### Problem: Can't see older transactions

**Explanation:**
- Tree shows recent transactions
- Scroll right to see older ones

**Solution:**
- Horizontal scroll is available
- Or check Transactions tab for full history

## 📊 Comparison with Other Views

| View | Best For | Shows |
|------|----------|-------|
| **Transaction Tree** | Visual flow, branching | How transactions relate |
| **Transactions Tab** | Detailed list | All transaction data |
| **Query History** | Query details | What was executed |
| **Analytics** | Statistics | Performance metrics |

**Use Tree for**: Understanding concurrency patterns, debugging conflicts, teaching MVCC

## 🎉 Best Practices

### 1. Keep Tree Open While Developing
```
Monitor in real-time as you test
Catch issues immediately
```

### 2. Use for Team Demos
```
Visual representation is easier to understand
Great for explaining MVCC to others
```

### 3. Debug with Tree + Transactions Tab
```
Tree: See the visual pattern
Transactions Tab: Get detailed information
```

### 4. Test Concurrent Scenarios
```
Open multiple tabs
Start transactions in each
Watch them branch and interact
```

## 🚀 Advanced Usage

### Scenario 1: Load Testing

```bash
# Terminal 1: Start many transactions
for i in {1..10}; do
  # Start transaction
  # Execute queries
  # Commit or rollback
done

# Watch the tree fill with branches!
```

### Scenario 2: Deadlock Detection

```
If two transactions wait for each other:
- Both will stay active (blue)
- Branches will remain open
- Visual indicator of potential deadlock
```

### Scenario 3: Performance Tuning

```
Compare:
- Wide tree (many concurrent) = Good throughput
- Tall tree (long transactions) = Potential bottleneck
- Many red nodes = High abort rate (investigate)
```

## 📚 Related Documentation

- **Backend API**: `backend/main.py` - WebSocket implementation
- **MVCC Engine**: `engine/mvcc_enhanced.py` - Transaction management
- **Frontend Component**: `frontend/src/components/TransactionTree.jsx`

## 🎓 Learning Resources

### Understand MVCC
- Watch branches to see concurrent execution
- See how transactions don't block each other
- Visual proof of MVCC in action

### Understand Isolation Levels
- Each node shows its isolation level
- Compare behavior visually
- See which transactions conflict

### Understand Transaction Lifecycle
- BEGIN: Branch appears
- ACTIVE: Blue node
- COMMIT: Merges with green
- ROLLBACK: Marked red

---

## 🎯 Quick Reference

```
Symbol          Meaning
──────────────────────────────────
●               Transaction node
───             Connection line
╱ or ╲         Branch/merge curve
🔵 Blue         Active
🟢 Green        Committed  
🔴 Red          Aborted
→               Direction of flow
#N              Transaction ID
```

---

**Enjoy your Git-like transaction visualization!** 🌳✨

For questions or issues, check the main README.md or inspect the browser console for WebSocket messages.

