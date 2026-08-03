import { useEffect, useMemo, useState } from "react";
import {
  Braces,
  Camera,
  ChevronRight,
  Clock3,
  Copy,
  Download,
  Eye,
  Loader2,
  Mail,
  Power,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { api, type AccountRecord } from "@/lib/api";
import { copyText, formatDuration, maskSecret } from "@/lib/utils";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  EmptyState,
  Input,
  PageHeader,
  Select,
  Toast,
} from "@/components/ui";

function statusVariant(status: string) {
  if (status === "success") return "success" as const;
  if (status === "failure") return "destructive" as const;
  if (status === "cancelled") return "warning" as const;
  return "secondary" as const;
}

function cpaVariant(status: string) {
  if (status === "success") return "success" as const;
  if (status === "failed" || status === "rejected") return "destructive" as const;
  if (status === "disabled") return "secondary" as const;
  return "warning" as const;
}

function emailDisableVariant(status: string) {
  if (status === "success") return "success" as const;
  if (status === "failed") return "destructive" as const;
  if (status === "skipped_cpa" || status === "not_attempted") return "warning" as const;
  return "secondary" as const;
}

function emailDisableLabel(status: string) {
  const labels: Record<string, string> = {
    success: "已停用",
    failed: "停用失败",
    skipped_cpa: "CPA 未成功",
    feature_disabled: "功能关闭",
    unsupported_source: "非 accounts",
    not_attempted: "未执行",
    not_applicable: "不适用",
  };
  return labels[status] || status || "-";
}

function AccountDetails({
  detail,
  showPassword,
  onTogglePassword,
  onCopy,
  onCopyAuthJson,
  onDownloadAuthJson,
  authJsonLoading,
}: {
  detail: AccountRecord;
  showPassword: boolean;
  onTogglePassword: () => void;
  onCopy: (value: string, label: string) => void;
  onCopyAuthJson: (kind: "cpa" | "grok2api") => void;
  onDownloadAuthJson: (kind: "cpa" | "grok2api") => void;
  authJsonLoading: "" | "copy-cpa" | "copy-grok2api" | "download-cpa" | "download-grok2api";
}) {
  const fields: Array<[string, string]> = [
    ["邮箱", detail.email],
    ["密码", showPassword ? detail.password : maskSecret(detail.password)],
    ["状态", detail.status],
    ["CPA", detail.cpa_status],
    ["服务商", detail.provider],
    ["NSFW", detail.nsfw_status],
    ["账号文件", detail.account_file],
    ["Auth 路径", detail.auth_path],
    ["CPA JSON 路径", detail.cpa_auth_path],
    ["Grok2API JSON 路径", detail.grok2api_auth_path],
    ["Auth 信息", detail.auth_info],
    ["邮箱池账号 ID", detail.email_account_id],
    ["邮箱停用状态", emailDisableLabel(detail.email_disable_status)],
    ["邮箱停用时间", detail.email_disabled_at],
    ["邮箱停用错误", detail.email_disable_error],
    ["失败类型", detail.failure_type],
    ["失败原因", detail.failure_reason],
    ["失败截图路径", detail.screenshot_path],
    ["Batch", detail.batch_id],
    ["来源", detail.source],
  ];

  return (
    <div className="space-y-4 text-sm">
      <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-3">
        <div className="break-all font-medium text-foreground">{detail.email || "未记录邮箱"}</div>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge variant={statusVariant(detail.status)}>{detail.status || "unknown"}</Badge>
          <Badge variant={cpaVariant(detail.cpa_status)}>CPA {detail.cpa_status || "-"}</Badge>
          <Badge variant={emailDisableVariant(detail.email_disable_status)}>
            邮箱 {emailDisableLabel(detail.email_disable_status)}
          </Badge>
        </div>
      </div>

      {detail.screenshot_url ? (
        <div className="overflow-hidden rounded-xl border border-rose-200 bg-rose-50/50">
          <div className="flex items-center gap-2 border-b border-rose-200 px-3 py-2 text-sm font-medium text-rose-800">
            <Camera className="h-4 w-4" aria-hidden="true" />
            浏览器失败现场
          </div>
          <a href={detail.screenshot_url} target="_blank" rel="noreferrer" title="在新窗口查看原图">
            <img
              src={detail.screenshot_url}
              alt={`注册失败截图 ${detail.email || detail.id}`}
              className="max-h-[28rem] w-full bg-slate-100 object-contain"
              loading="lazy"
            />
          </a>
          <div className="px-3 py-2 text-xs text-muted-foreground">点击截图可在新窗口查看原图</div>
        </div>
      ) : null}

      <div className="rounded-xl border border-violet-100 bg-violet-50/60 p-3">
        <div className="flex items-start gap-2">
          <Braces className="mt-0.5 h-4 w-4 shrink-0 text-violet-600" aria-hidden="true" />
          <div>
            <div className="text-sm font-medium text-foreground">授权 JSON</div>
            <p className="mt-0.5 text-xs leading-5 text-muted-foreground">
              可复制完整 JSON 内容，也可将原始 JSON 文件下载到本地。
            </p>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          <Button
            variant="outline"
            onClick={() => onCopyAuthJson("cpa")}
            disabled={!!authJsonLoading}
          >
            {authJsonLoading === "copy-cpa" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Copy className="h-4 w-4" aria-hidden="true" />
            )}
            复制 CPA JSON
          </Button>
          <Button variant="outline" onClick={() => onDownloadAuthJson("cpa")} disabled={!!authJsonLoading}>
            {authJsonLoading === "download-cpa" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-4 w-4" aria-hidden="true" />
            )}
            下载 CPA JSON
          </Button>
          <Button
            variant="outline"
            onClick={() => onCopyAuthJson("grok2api")}
            disabled={!!authJsonLoading}
          >
            {authJsonLoading === "copy-grok2api" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Copy className="h-4 w-4" aria-hidden="true" />
            )}
            复制 Grok2API JSON
          </Button>
          <Button variant="outline" onClick={() => onDownloadAuthJson("grok2api")} disabled={!!authJsonLoading}>
            {authJsonLoading === "download-grok2api" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-4 w-4" aria-hidden="true" />
            )}
            下载 Grok2API JSON
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        {fields.map(([label, value]) => (
          <div key={label} className="rounded-xl border bg-muted/30 p-3">
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="text-xs font-medium text-muted-foreground">{label}</span>
              <Button
                size="sm"
                variant="ghost"
                className="h-9 w-9 min-h-9 px-0"
                onClick={() => onCopy(String(value || ""), label)}
                aria-label={`复制${label}`}
              >
                <Copy className="h-3.5 w-3.5" aria-hidden="true" />
              </Button>
            </div>
            <div className="break-all whitespace-pre-wrap leading-6 text-foreground">{value || "-"}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" onClick={onTogglePassword}>
          <Eye className="h-4 w-4" aria-hidden="true" />
          {showPassword ? "隐藏密码" : "显示密码"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => onCopy(`${detail.email}----${detail.password}`, "邮箱密码")}
        >
          <Copy className="h-4 w-4" aria-hidden="true" />
          复制账号
        </Button>
      </div>
    </div>
  );
}

export function AccountsPage() {
  const [items, setItems] = useState<AccountRecord[]>([]);
  const [status, setStatus] = useState("");
  const [emailDisableStatus, setEmailDisableStatus] = useState("");
  const [keyword, setKeyword] = useState("");
  const [selected, setSelected] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<AccountRecord | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [authJsonLoading, setAuthJsonLoading] = useState<
    "" | "copy-cpa" | "copy-grok2api" | "download-cpa" | "download-grok2api"
  >("");
  const [visibleCount, setVisibleCount] = useState(50);
  const [toast, setToast] = useState<{ message: string; tone?: "default" | "success" | "error" }>({
    message: "",
  });

  const selectedIds = useMemo(
    () => Object.entries(selected).filter(([, value]) => value).map(([key]) => Number(key)),
    [selected]
  );
  const allVisibleSelected = items.length > 0 && items.every((item) => selected[item.id]);
  const visibleItems = items.slice(0, visibleCount);

  const showToast = (message: string, tone: "default" | "success" | "error" = "default") => {
    setToast({ message, tone });
    window.setTimeout(() => setToast({ message: "" }), 2200);
  };

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.accounts({
        status,
        emailDisableStatus,
        q: keyword,
        limit: 1000,
      });
      setItems(data.items || []);
      setVisibleCount(50);
      if (detail) {
        setDetail((data.items || []).find((item) => item.id === detail.id) || null);
      }
    } catch (err: any) {
      showToast(err.message || "加载失败", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!detail) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDetail(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [detail]);

  const toggleAll = (checked: boolean) => {
    setSelected((previous) => {
      const next = { ...previous };
      for (const item of items) {
        if (checked) next[item.id] = true;
        else delete next[item.id];
      }
      return next;
    });
  };

  const onCopy = async (value: string, label: string) => {
    const ok = await copyText(value);
    showToast(ok ? `已复制${label}` : "复制失败", ok ? "success" : "error");
  };

  const onCopyAuthJson = async (kind: "cpa" | "grok2api") => {
    if (!detail) return;
    setAuthJsonLoading(`copy-${kind}` as "copy-cpa" | "copy-grok2api");
    try {
      const result = await api.accountAuthJson(detail.id, kind);
      const ok = await copyText(result.content);
      const label = kind === "cpa" ? "CPA JSON" : "Grok2API JSON";
      showToast(ok ? `已复制${label}` : `${label}复制失败`, ok ? "success" : "error");
    } catch (err: any) {
      showToast(err.message || "读取授权 JSON 失败", "error");
    } finally {
      setAuthJsonLoading("");
    }
  };

  const onDownloadAuthJson = async (kind: "cpa" | "grok2api") => {
    if (!detail) return;
    setAuthJsonLoading(`download-${kind}` as "download-cpa" | "download-grok2api");
    try {
      const result = await api.downloadAccountAuthJson(detail.id, kind);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      showToast(`已下载${kind === "cpa" ? "CPA JSON" : "Grok2API JSON"}`, "success");
    } catch (err: any) {
      showToast(err.message || "下载授权 JSON 失败", "error");
    } finally {
      setAuthJsonLoading("");
    }
  };

  const onDelete = async () => {
    if (!selectedIds.length) {
      showToast("请先选择记录", "error");
      return;
    }
    if (!window.confirm(`删除 ${selectedIds.length} 条记录及其关联文件？此操作不可恢复。`)) return;
    try {
      const result = await api.deleteAccounts(selectedIds, true);
      showToast(`已删除 ${result.deleted} 条，文件 ${result.deleted_files} 个`, "success");
      setSelected({});
      setDetail(null);
      await load();
    } catch (err: any) {
      showToast(err.message || "删除失败", "error");
    }
  };

  return (
    <div className="space-y-5 sm:space-y-6">
      <PageHeader
        title="账号管理"
        description="筛选和查看注册结果，在手机端使用卡片列表，在大屏设备上使用数据表格。"
        actions={
          <>
            <Button variant="outline" onClick={load} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
              刷新
            </Button>
            <Button variant="destructive" onClick={onDelete} disabled={!selectedIds.length}>
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              删除 ({selectedIds.length})
            </Button>
          </>
        }
      />

      <Card>
        <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-[160px_190px_minmax(0,1fr)_auto]">
          <Select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="按状态筛选">
            <option value="">全部状态</option>
            <option value="success">success</option>
            <option value="failure">failure</option>
            <option value="skipped">skipped</option>
            <option value="cancelled">cancelled</option>
          </Select>
          <Select
            value={emailDisableStatus}
            onChange={(e) => setEmailDisableStatus(e.target.value)}
            aria-label="按邮箱停用状态筛选"
          >
            <option value="">全部停用状态</option>
            <option value="success">已停用</option>
            <option value="failed">停用失败</option>
            <option value="skipped_cpa">CPA 未成功</option>
            <option value="feature_disabled">功能关闭</option>
            <option value="unsupported_source">非 accounts</option>
            <option value="not_attempted">未执行</option>
            <option value="not_applicable">不适用</option>
          </Select>
          <div className="relative min-w-0 sm:col-span-2 lg:col-span-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              className="pl-9"
              type="search"
              placeholder="搜索邮箱、服务商、失败原因或 Batch"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") load();
              }}
              aria-label="搜索账号记录"
            />
          </div>
          <Button className="sm:col-span-2 lg:col-span-1" onClick={load} disabled={loading}>
            <Search className="h-4 w-4" aria-hidden="true" />
            查询
          </Button>
        </CardContent>
      </Card>

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(340px,0.85fr)]">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader className="flex-row items-center justify-between gap-3">
            <div>
              <CardTitle>注册记录</CardTitle>
              <CardDescription>共 {items.length} 条，手机端每次展示 50 条。</CardDescription>
            </div>
            <label className="flex min-h-11 cursor-pointer items-center gap-2 rounded-xl px-2 text-sm text-muted-foreground hover:bg-muted xl:hidden">
              <input
                type="checkbox"
                checked={allVisibleSelected}
                onChange={(e) => toggleAll(e.target.checked)}
              />
              全选
            </label>
          </CardHeader>
          <CardContent className="p-0">
            {items.length === 0 ? (
              <div className="p-4 sm:p-6">
                <EmptyState title="暂无账号记录" description="启动注册后，成功或失败结果会显示在这里。" />
              </div>
            ) : (
              <>
                <div className="divide-y xl:hidden">
                  {visibleItems.map((item) => (
                    <article key={item.id} className="space-y-3 p-4">
                      <div className="flex items-start gap-3">
                        <label className="flex h-11 w-8 shrink-0 cursor-pointer items-center justify-center" aria-label={`选择 ${item.email}`}>
                          <input
                            type="checkbox"
                            checked={!!selected[item.id]}
                            onChange={(e) =>
                              setSelected((prev) => ({ ...prev, [item.id]: e.target.checked }))
                            }
                          />
                        </label>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start gap-2">
                            <Mail className="mt-1 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                            <div className="break-all font-medium leading-6 text-foreground">{item.email || "-"}</div>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2">
                            <Badge variant={statusVariant(item.status)}>{item.status}</Badge>
                            <Badge variant={cpaVariant(item.cpa_status)}>CPA {item.cpa_status || "-"}</Badge>
                            <Badge variant={emailDisableVariant(item.email_disable_status)}>
                              <Power className="mr-1 h-3 w-3" aria-hidden="true" />
                              {emailDisableLabel(item.email_disable_status)}
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 rounded-xl bg-muted/40 p-3 text-xs leading-5 text-muted-foreground">
                        <div>
                          <span className="block">服务商</span>
                          <strong className="block truncate font-medium text-foreground">{item.provider || "-"}</strong>
                        </div>
                        <div>
                          <span className="block">耗时</span>
                          <strong className="block font-medium text-foreground">{formatDuration(item.duration_seconds)}</strong>
                        </div>
                        <div className="col-span-2 flex items-start gap-1.5 border-t pt-2">
                          <Clock3 className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                          <span className="break-all">{item.finished_at || "未记录完成时间"}</span>
                        </div>
                      </div>

                      <Button variant="outline" className="w-full justify-between" onClick={() => setDetail(item)}>
                        查看账号详情
                        <ChevronRight className="h-4 w-4" aria-hidden="true" />
                      </Button>
                    </article>
                  ))}
                  {visibleCount < items.length ? (
                    <div className="p-4">
                      <Button
                        variant="secondary"
                        className="w-full"
                        onClick={() => setVisibleCount((value) => Math.min(value + 50, items.length))}
                      >
                        加载更多（剩余 {items.length - visibleCount}）
                      </Button>
                    </div>
                  ) : null}
                </div>

                <div className="hidden max-h-[720px] overflow-auto xl:block">
                  <table className="w-full min-w-[860px] text-left text-sm">
                    <thead className="sticky top-0 z-10 bg-card shadow-[0_1px_0_hsl(var(--border))]">
                      <tr className="text-xs font-medium text-muted-foreground">
                        <th className="w-12 px-4 py-3">
                          <input
                            type="checkbox"
                            checked={allVisibleSelected}
                            onChange={(e) => toggleAll(e.target.checked)}
                            aria-label="全选当前记录"
                          />
                        </th>
                        <th className="px-3 py-3">邮箱</th>
                        <th className="px-3 py-3">状态</th>
                        <th className="px-3 py-3">邮箱停用</th>
                        <th className="px-3 py-3">服务商</th>
                        <th className="px-3 py-3">耗时</th>
                        <th className="sticky right-0 z-20 w-20 border-l bg-card px-3 py-3 shadow-[-8px_0_16px_-14px_rgba(15,23,42,0.55)]">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => (
                        <tr
                          key={item.id}
                          className={`group border-b transition-colors hover:bg-muted/45 ${detail?.id === item.id ? "bg-blue-50/70" : ""}`}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={!!selected[item.id]}
                              onChange={(e) =>
                                setSelected((prev) => ({ ...prev, [item.id]: e.target.checked }))
                              }
                              aria-label={`选择 ${item.email}`}
                            />
                          </td>
                          <td className="max-w-[250px] px-3 py-3">
                            <div className="truncate font-medium text-foreground" title={item.email}>{item.email || "-"}</div>
                            <div className="mt-0.5 truncate text-xs text-muted-foreground">{item.finished_at || "-"}</div>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex flex-col items-start gap-1.5">
                              <Badge variant={statusVariant(item.status)}>{item.status}</Badge>
                              <Badge variant={cpaVariant(item.cpa_status)}>CPA {item.cpa_status || "-"}</Badge>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <Badge variant={emailDisableVariant(item.email_disable_status)}>
                              {emailDisableLabel(item.email_disable_status)}
                            </Badge>
                            {item.email_disable_error ? (
                              <div
                                className="mt-1 max-w-[180px] truncate text-xs text-red-600"
                                title={item.email_disable_error}
                              >
                                {item.email_disable_error}
                              </div>
                            ) : null}
                          </td>
                          <td className="px-3 py-3 text-muted-foreground">{item.provider || "-"}</td>
                          <td className="px-3 py-3 tabular-nums text-muted-foreground">{formatDuration(item.duration_seconds)}</td>
                          <td className={`sticky right-0 z-[5] border-l px-3 py-3 shadow-[-8px_0_16px_-14px_rgba(15,23,42,0.55)] ${detail?.id === item.id ? "bg-blue-50" : "bg-card group-hover:bg-muted"}`}>
                            <Button size="sm" variant="ghost" onClick={() => setDetail(item)}>
                              查看
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="sticky top-24 hidden max-h-[calc(100dvh-8rem)] overflow-hidden xl:block">
          <CardHeader>
            <CardTitle>账号详情</CardTitle>
            <CardDescription>选择一条记录后，可查看并复制完整字段。</CardDescription>
          </CardHeader>
          <CardContent className="max-h-[calc(100dvh-14rem)] overflow-auto">
            {!detail ? (
              <EmptyState title="未选择记录" description="从左侧表格选择一条账号记录。" />
            ) : (
              <AccountDetails
                detail={detail}
                showPassword={showPassword}
                onTogglePassword={() => setShowPassword((value) => !value)}
                onCopy={onCopy}
                onCopyAuthJson={onCopyAuthJson}
                onDownloadAuthJson={onDownloadAuthJson}
                authJsonLoading={authJsonLoading}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {detail ? (
        <div
          className="fixed inset-0 z-[70] flex items-end bg-slate-950/40 xl:hidden"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setDetail(null);
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="account-detail-title"
            className="max-h-[92dvh] w-full overflow-hidden rounded-t-3xl bg-card shadow-2xl"
          >
            <div className="mx-auto mt-2 h-1.5 w-12 rounded-full bg-slate-300" />
            <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b bg-card px-4 py-3">
              <div className="min-w-0">
                <h2 id="account-detail-title" className="font-semibold text-foreground">账号详情</h2>
                <p className="truncate text-xs text-muted-foreground">{detail.email || "未记录邮箱"}</p>
              </div>
              <Button size="icon" variant="ghost" onClick={() => setDetail(null)} aria-label="关闭账号详情">
                <X className="h-5 w-5" aria-hidden="true" />
              </Button>
            </header>
            <div className="max-h-[calc(92dvh-74px)] overflow-y-auto px-4 pb-[calc(1.5rem+env(safe-area-inset-bottom))] pt-4">
              <AccountDetails
                detail={detail}
                showPassword={showPassword}
                onTogglePassword={() => setShowPassword((value) => !value)}
                onCopy={onCopy}
                onCopyAuthJson={onCopyAuthJson}
                onDownloadAuthJson={onDownloadAuthJson}
                authJsonLoading={authJsonLoading}
              />
            </div>
          </section>
        </div>
      ) : null}

      <Toast message={toast.message} tone={toast.tone} />
    </div>
  );
}
