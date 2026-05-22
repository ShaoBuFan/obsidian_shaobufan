---
tags:
  - ReactHook
  - ReactHook/appendix
created: 2026-05-22
---
# 附录 B: 快速参考

## 内置 Hook 速查

| Hook | 签名 | 一句话 | 何时用 | 何时不用 |
|------|------|--------|--------|----------|
| useState | `const [v, setV] = useState(init)` | 带遥控器的盒子 | 值需要保持且变化触发渲染 | 值不需要触发渲染、值可推导 |
| useEffect | `useEffect(fn, deps)` | 画干之后做家务 | 与外部世界同步 | 事件处理、可推导值 |
| useRef | `const ref = useRef(init)` | 秘密口袋 | 值需要保持但不触发渲染 | 值需要触发渲染 |
| useMemo | `const v = useMemo(fn, deps)` | 记住答案 | 昂贵计算、引用稳定 | 简单计算、无性能问题 |
| useCallback | `const fn = useCallback(fn, deps)` | 记住函数 | memo 子组件 prop、effect 依赖 | 普通事件处理器 |
| useReducer | `const [s, d] = useReducer(r, init)` | 正规的盒子 | 复杂状态逻辑、多 action | 简单 state |
| useLayoutEffect | `useLayoutEffect(fn, deps)` | 绘制前执行 | 避免闪烁 | 默认用 useEffect |
| useContext | `const v = useContext(Ctx)` | 对讲机 | 跨层级传值 | 只有一两层传值 |

## 五大模式速查

| 模式 | 信号 | 内部 Hook | 典型输出 | 例子 |
|------|------|-----------|----------|------|
| Wrapper | "简化 API" | 1 个内置 Hook | 语义化方法 | useToggle, useCounter |
| Composer | "创造新行为" | 2-3 个不同 Hook | 新能力 | useDebounce, usePrevious |
| Extractor | "移出组件" | 1-2 个 Hook | 即用型函数 | useDocumentTitle, useEventListener |
| Facade | "打包服务" | 3+ 个 Hook | 对象 | useAuth, useLocalStorage |
| Coordinator | "协调互动" | 多个 Hook + 逻辑 | 对象 + 方法 | useForm |

## 六步设计法速查

| 步骤 | 问自己 | 产出 |
|------|--------|------|
| 1. 识别响应式值 | "什么会变化？" | 值清单 |
| 2. 分类每个值 | "变化时该怎样？" | 类别映射表 |
| 3. 设计契约 | "输入什么？输出什么？" | 类型签名 |
| 4. 选择原语 | "用什么 Hook？" | 依赖图 |
| 5. 实现 | "按顺序写出来" | 代码 |
| 6. 审查 | "追踪检查" | 验证清单 |

## 反模式速查

| 反模式 | 症状 | 修复 |
|--------|------|------|
| ==过期闭包== | 函数读到旧值 | 函数式更新 / useRef / 补 deps |
| useEffect 算派生值 | 渲染两次，第一次值过期 | 渲染期间直接计算 |
| useEffect 处理事件 | 行为逻辑在 effect 中 | 移到事件处理器 |
| 缺失依赖 | lint 警告 | 补全 deps 或重构 |
| ==过度抽象== | Hook 只被用一次且没简化 | 内联回组件 |
| ==上帝 Hook== | 返回 10+ 个值 | 拆成多个子 Hook |
| 冗余状态同步 | 两个 state 总是同变 | 单源真理 + 派生值 |

## useEffect 执行时机

```
挂载：     setup()
更新：     cleanup() → setup()
卸载：     cleanup()
```

## 常见类别代码骨架

### 数据获取

```javascript
function useFetch(url) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(url)
      .then(res => res.ok ? res.json() : Promise.reject(new Error(res.status)))
      .then(d => !cancelled && setData(d))
      .catch(e => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [url]);

  return { data, error, loading };
}
```

### DOM 事件监听

```javascript
function useEventListener(target, event, handler) {
  const savedHandler = useRef(handler);
  useEffect(() => { savedHandler.current = handler; }, [handler]);

  useEffect(() => {
    const el = target?.current ?? target;
    if (!el?.addEventListener) return;
    const listener = e => savedHandler.current(e);
    el.addEventListener(event, listener);
    return () => el.removeEventListener(event, listener);
  }, [target, event]);
}
```

### 浏览器 API 同步

```javascript
function useBrowserAPI(apiReadFn, apiSubscribeFn) {
  const [value, setValue] = useState(apiReadFn);
  useEffect(() => {
    return apiSubscribeFn(setValue);
  }, []);
  return value;
}
```

### 计时器

```javascript
function useInterval(callback, delay) {
  const savedCallback = useRef(callback);
  useEffect(() => { savedCallback.current = callback; }, [callback]);

  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
```

### 表单

```javascript
function useField(initialValue = '') {
  const [value, setValue] = useState(initialValue);
  const [touched, setTouched] = useState(false);
  const onChange = useCallback(e => setValue(e.target.value), []);
  const onBlur = useCallback(() => setTouched(true), []);
  return { value, touched, onChange, onBlur };
}
```
