# 🎯 Avatar Quota System - 20 Minutes Total Per Account

## 📊 **Updated System Overview**

The avatar usage tracking system has been updated to implement a **simple 20-minute total limit per account** (not monthly).

---

## 🔧 **Key Changes Made**

### **1. Database Model Updates** (`avatar_usage.py`)
```python
class UsageQuota(BaseModel):
    """User's avatar usage quota - 20 minutes total per account."""
    
    # Total account limits (lifetime)
    total_limit_minutes: int = Field(default=20, description="Total limit in minutes (20 min per account)")
    
    # Current usage (lifetime)
    used_minutes: int = Field(default=0, description="Total minutes used")
    used_seconds: int = Field(default=0, description="Total seconds used (for precision)")
    session_count: int = Field(default=0, description="Total number of sessions")
    
    # Status
    quota_exhausted: bool = Field(default=False, description="Whether 20-minute limit reached")
    exhausted_at: Optional[datetime] = Field(None, description="When quota was exhausted")
```

### **2. Repository Updates** (`avatar_usage_repository.py`)
```python
# Simplified quota creation - one per user, lifetime
async def get_or_create_quota(self, user_id: str) -> UsageQuota:
    # Creates 20-minute total quota per user (not monthly)
    
# Updated usage tracking
async def update_quota_usage(self, user_id: str, duration_seconds: int):
    # Accumulates total seconds used across all sessions
    # Marks quota_exhausted=True when >= 20 minutes reached
    
# Simplified quota checking
async def check_quota_limits(self, user_id: str):
    # Returns can_create_session=False if quota_exhausted=True
```

---

## ⚡ **How It Works**

### **Account Creation:**
- New user gets **20 minutes total** streaming time
- No monthly resets - this is lifetime limit

### **Session Tracking:**
- Each streaming session consumes from the 20-minute pool
- Precise tracking down to seconds for accuracy
- When total reaches 1200 seconds (20 minutes), quota is exhausted

### **Quota Enforcement:**
```python
# Before starting any session:
quota_check = await usage_repo.check_quota_limits(user_id)

if quota_check["quota_exhausted"]:
    # Force user to static avatar permanently
    return {"switch_to_static": True}
```

### **Example Usage Scenarios:**
```
User starts with: 20:00 minutes available

Session 1: 5:30 minutes → 14:30 remaining
Session 2: 8:15 minutes → 6:15 remaining  
Session 3: 6:15 minutes → 0:00 remaining ❌ QUOTA EXHAUSTED

All future sessions: Static avatar only
```

---

## 🚨 **Critical Behaviors**

### **1. Permanent Exhaustion:**
- Once 20 minutes used, user **cannot create new streaming sessions**
- All future avatar interactions use **static avatar only**
- No reset mechanism (unless manually reset by admin)

### **2. Session Termination:**
- Individual sessions still have 20-minute **per-session** timeout
- But total quota may be exhausted before session timeout
- Example: User has 2 minutes left → session auto-ends after 2 minutes

### **3. Precise Tracking:**
- Tracks both `used_seconds` and `used_minutes` for accuracy
- Prevents gaming the system with multiple short sessions

---

## 📱 **Frontend Integration**

### **Quota Check Before Session:**
```typescript
// Before starting HeyGen avatar
const quotaResponse = await fetch('/api/v1/avatar/quota/check', {
    method: 'POST',
    body: JSON.stringify({ vertex_session_id: sessionId })
});

const quota = await quotaResponse.json();

if (quota.warnings.quota_exhausted) {
    // Force static avatar - no streaming allowed
    setUseStaticAvatar(true);
    showQuotaExhaustedMessage();
    return;
}

// Show remaining time: "You have 12:30 minutes remaining"
showRemainingTime(quota.limits.minutes_remaining, quota.limits.seconds_remaining);
```

### **Real-Time Monitoring:**
```typescript
// Optional: Show countdown during session
const remainingTime = quota.limits.seconds_remaining;
// Display: "Quota: 12:30 remaining" 

// When quota exhausted during session:
if (sessionEndResponse.switch_to_static) {
    setUseStaticAvatar(true);
    showMessage("Quota exhausted - switched to static avatar");
}
```

---

## 🎯 **Benefits of This System**

### **✅ Simplicity:**
- No complex monthly billing cycles
- Clear, understandable limit: "20 minutes total"
- Easy to explain to users

### **✅ Cost Control:**
- Hard cap prevents unlimited HeyGen charges
- Predictable costs: Max 20 minutes per user ever

### **✅ Fair Usage:**
- Prevents abuse of streaming avatar feature
- Encourages thoughtful use of premium feature

### **✅ Graceful Degradation:**
- Users don't lose functionality - they get static avatar
- No service interruption when quota exhausted

---

## 🔧 **Database Migration Needed**

The `usage_quotas` table needs to be updated to remove monthly fields and add the new lifetime tracking fields:

```sql
-- Remove monthly columns
ALTER TABLE usage_quotas DROP COLUMN current_month;
ALTER TABLE usage_quotas DROP COLUMN monthly_limit_minutes;
ALTER TABLE usage_quotas DROP COLUMN monthly_limit_cost;
ALTER TABLE usage_quotas DROP COLUMN used_cost;
ALTER TABLE usage_quotas DROP COLUMN last_reset_at;

-- Add lifetime tracking columns
ALTER TABLE usage_quotas ADD COLUMN total_limit_minutes INTEGER DEFAULT 20;
ALTER TABLE usage_quotas ADD COLUMN used_seconds INTEGER DEFAULT 0;
ALTER TABLE usage_quotas ADD COLUMN quota_exhausted BOOLEAN DEFAULT FALSE;
ALTER TABLE usage_quotas ADD COLUMN exhausted_at TIMESTAMP;
```

---

## 💡 **Summary**

The updated system provides:
- **20 minutes total** streaming time per account (lifetime)
- **Permanent quota exhaustion** after limit reached
- **Automatic fallback** to static avatar
- **Precise second-level tracking**
- **Simple, predictable cost control**

This ensures users get a premium experience within controlled limits, and the system gracefully handles quota exhaustion without service disruption. 🎯 