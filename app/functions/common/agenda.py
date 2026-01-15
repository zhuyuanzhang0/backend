import datetime as _dt

def _utc_now_dtstamp() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def _format_dt_local(dt: _dt.datetime) -> str:
    # iCalendar DATE-TIME 基本格式：YYYYMMDDTHHMMSS
    return dt.strftime("%Y%m%dT%H%M%S")

def _format_date(d: _dt.date) -> str:
    return d.strftime("%Y%m%d")

def _to_datetime(v):
    """
    pymysql DictCursor 通常会把 DATETIME/TIMESTAMP 转成 datetime；
    如果你这里拿到的是字符串，也兼容解析。
    """
    if v is None:
        return None
    if isinstance(v, _dt.datetime):
        return v
    if isinstance(v, _dt.date) and not isinstance(v, _dt.datetime):
        return _dt.datetime(v.year, v.month, v.day, 0, 0, 0)
    if isinstance(v, str):
        # 兼容 "YYYY-MM-DD HH:MM:SS" / "YYYY-MM-DD"
        s = v.strip()
        if len(s) == 10:
            return _dt.datetime.strptime(s, "%Y-%m-%d")
        return _dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    raise TypeError(f"Unsupported datetime value: {type(v)}")

def _fold_ical_line(line: str, limit_octets: int = 75) -> str:
    """
    iCalendar 行折叠：每行 <= 75 octets（UTF-8 计字节），续行以 CRLF + 空格开头
    """
    b = line.encode("utf-8")
    if len(b) <= limit_octets:
        return line

    parts = []
    cur = ""
    cur_bytes = 0

    for ch in line:
        cb = ch.encode("utf-8")
        if cur_bytes + len(cb) > limit_octets:
            parts.append(cur)
            cur = ch
            cur_bytes = len(cb)
        else:
            cur += ch
            cur_bytes += len(cb)

    if cur:
        parts.append(cur)

    # 续行以一个空格开头
    return "\r\n ".join(parts)

def _prop(name: str, value: str, params: dict | None = None) -> str:
    """
    生成属性行：NAME(;PARAM=...):VALUE
    自动折行（folding）
    """
    if value is None:
        return ""
    params_str = ""
    if params:
        params_str = "".join([f";{k}={v}" for k, v in params.items()])
    line = f"{name}{params_str}:{value}"
    return _fold_ical_line(line)

def export_ics(
    table_name: str,
    cal_name: str = "zzz",
    tzid: str = "Asia/Shanghai",
    db_name: str = "agenda",
    include_todos: bool = True,
) -> str:
    """
    从用户表导出 .ics 文本（VEVENT + 可选 VTODO）
    """
    table_name = _safe_table_name(table_name)

    conn = get_conn(db_name)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(f"SELECT * FROM `{table_name}` ORDER BY COALESCE(dtstart, due), created_at")
            rows = cursor.fetchall()
    finally:
        conn.close()

    now_stamp = _utc_now_dtstamp()
    vtimezone_last_modified = _utc_now_dtstamp()

    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append(_prop("PRODID", "-//your.app//Agenda Plugin//EN"))
    lines.append(_prop("X-WR-CALNAME", cal_name))
    lines.append(_prop("NAME", cal_name))
    lines.append(_prop("REFRESH-INTERVAL", "P5M", params={"VALUE": "DURATION"}))
    lines.append("CALSCALE:GREGORIAN")

    # VTIMEZONE（按你示例的 Asia/Shanghai 模板输出）
    lines.append("BEGIN:VTIMEZONE")
    lines.append(_prop("TZID", tzid))
    lines.append(_prop("LAST-MODIFIED", vtimezone_last_modified))
    lines.append(_prop("TZURL", f"https://www.tzurl.org/zoneinfo-outlook/{tzid}"))
    lines.append(_prop("X-LIC-LOCATION", tzid))
    lines.append("BEGIN:STANDARD")
    lines.append(_prop("TZNAME", "CST"))
    lines.append(_prop("TZOFFSETFROM", "+0800"))
    lines.append(_prop("TZOFFSETTO", "+0800"))
    lines.append(_prop("DTSTART", "19700101T000000"))
    lines.append("END:STANDARD")
    lines.append("END:VTIMEZONE")

    for r in rows:
        kind = (r.get("kind") or "").upper()
        if kind == "VTODO" and not include_todos:
            continue
        if kind not in ("VEVENT", "VTODO"):
            # 不认识的类型直接跳过
            continue

        uid = r.get("uid")
        summary = r.get("summary") or ""
        description = r.get("description")
        location = r.get("location")
        all_day = int(r.get("all_day") or 0)

        if kind == "VEVENT":
            lines.append("BEGIN:VEVENT")
            lines.append(_prop("DTSTAMP", now_stamp))
            lines.append(_prop("UID", uid))

            dtstart = _to_datetime(r.get("dtstart"))
            dtend = _to_datetime(r.get("dtend"))

            if all_day:
                if not dtstart:
                    # 没有开始时间就跳过（或你也可选择用 created_at）
                    lines.append("END:VEVENT")
                    continue
                d0 = dtstart.date()
                if dtend:
                    d1 = dtend.date()
                else:
                    d1 = d0 + _dt.timedelta(days=1)

                lines.append(_prop("DTSTART", _format_date(d0), params={"VALUE": "DATE"}))
                lines.append(_prop("DTEND", _format_date(d1), params={"VALUE": "DATE"}))
            else:
                if dtstart:
                    lines.append(_prop("DTSTART", _format_dt_local(dtstart), params={"TZID": tzid}))
                if dtend:
                    lines.append(_prop("DTEND", _format_dt_local(dtend), params={"TZID": tzid}))

            lines.append(_prop("SUMMARY", summary))
            if description:
                lines.append(_prop("DESCRIPTION", description))
            if location:
                lines.append(_prop("LOCATION", location))

            # 可选：重复/标签
            if r.get("rrule"):
                lines.append(_prop("RRULE", r["rrule"]))
            if r.get("exdate"):
                # 如果你存的是逗号分隔 20250101T...，这里直接输出；更严谨可拆分多行 EXDATE
                lines.append(_prop("EXDATE", r["exdate"], params={"TZID": tzid}))
            if r.get("categories"):
                lines.append(_prop("CATEGORIES", r["categories"]))

            lines.append("END:VEVENT")

        elif kind == "VTODO":
            lines.append("BEGIN:VTODO")
            lines.append(_prop("DTSTAMP", now_stamp))
            lines.append(_prop("UID", uid))
            lines.append(_prop("SUMMARY", summary))

            due = _to_datetime(r.get("due"))
            if due:
                lines.append(_prop("DUE", _format_dt_local(due), params={"TZID": tzid}))

            if description:
                lines.append(_prop("DESCRIPTION", description))
            if location:
                # VTODO 也允许 LOCATION（部分客户端可能忽略）
                lines.append(_prop("LOCATION", location))

            # 状态/优先级/进度
            if r.get("status"):
                lines.append(_prop("STATUS", str(r["status"])))
            if r.get("priority") is not None:
                lines.append(_prop("PRIORITY", str(int(r["priority"]))))
            if r.get("percent_complete") is not None:
                lines.append(_prop("PERCENT-COMPLETE", str(int(r["percent_complete"]))))

            # 重复/标签
            if r.get("rrule"):
                lines.append(_prop("RRULE", r["rrule"]))
            if r.get("exdate"):
                lines.append(_prop("EXDATE", r["exdate"], params={"TZID": tzid}))
            if r.get("categories"):
                lines.append(_prop("CATEGORIES", r["categories"]))

            lines.append("END:VTODO")

    lines.append("END:VCALENDAR")

    # 确保 CRLF 结尾
    return "\r\n".join([ln for ln in lines if ln]) + "\r\n"
