from __future__ import annotations

import csv
import io
import logging
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StationInfo:
    code: str
    longitude_deg: float | None = None
    latitude_deg: float | None = None


def _finite_time_mask(times: np.ndarray) -> np.ndarray:
    times = np.asarray(times)
    if np.issubdtype(times.dtype, np.datetime64):
        return ~np.isnat(times)
    return np.isfinite(times)


def parse_station_metadata(text: str) -> dict[str, StationInfo]:
    stations: dict[str, StationInfo] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        code = parts[0].strip()
        try:
            lon = float(parts[1]); lat = float(parts[2])
        except ValueError:
            continue
        stations[code] = StationInfo(code=code, longitude_deg=lon, latitude_deg=lat)
    return stations


def _read_text_from_source(source_path: str | Path, member_name: str | None = None) -> str:
    path = Path(source_path)
    if path.suffix.lower() == '.zip':
        if member_name is None:
            raise ValueError('member_name is required when reading from a zip archive.')
        with zipfile.ZipFile(path, 'r') as zf:
            return zf.read(member_name).decode('utf-8', errors='ignore')
    return path.read_text(encoding='utf-8', errors='ignore')


def _find_metadata_text(source_path: str | Path) -> tuple[str | None, str | None]:
    path = Path(source_path)
    if path.is_dir():
        for cand in [path / 'SG station.txt', path / 'sg station.txt']:
            if cand.exists():
                return cand.read_text(encoding='utf-8', errors='ignore'), str(cand)
        return None, None
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path, 'r') as zf:
            for name in zf.namelist():
                if Path(name).name.lower() == 'sg station.txt':
                    return zf.read(name).decode('utf-8', errors='ignore'), name
        return None, None
    parent = path.parent
    for cand in [parent / 'SG station.txt', parent / 'sg station.txt']:
        if cand.exists():
            return cand.read_text(encoding='utf-8', errors='ignore'), str(cand)
    return None, None


def list_stations_in_source(source_path: str | Path) -> list[dict[str, Any]]:
    path = Path(source_path)
    text, _ = _find_metadata_text(path)
    metadata = parse_station_metadata(text or '')
    station_codes: list[str] = []
    if path.is_dir():
        station_codes = sorted(p.stem for p in path.glob('*.ggp'))
    elif path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path, 'r') as zf:
            station_codes = sorted(Path(name).stem for name in zf.namelist() if name.lower().endswith('.ggp'))
    elif path.suffix.lower() in {'.ggp', '.csv'}:
        station_codes = [path.stem]
    else:
        raise ValueError(f'Unsupported source type: {path}')
    return [
        {
            'station_code': code,
            'longitude_deg': metadata.get(code, StationInfo(code=code)).longitude_deg,
            'latitude_deg': metadata.get(code, StationInfo(code=code)).latitude_deg,
        }
        for code in station_codes
    ]


def parse_ggp_lines(lines: Iterable[str]) -> tuple[np.ndarray, np.ndarray]:
    timestamps: list[np.datetime64] = []
    values: list[float] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        date_s, time_s, value_s = parts[0], parts[1], parts[2]
        if len(date_s) != 8 or len(time_s) != 6 or not date_s.isdigit() or not time_s.isdigit():
            continue
        try:
            ts = datetime.strptime(date_s + time_s, '%Y%m%d%H%M%S')
            val = float(value_s)
        except ValueError:
            continue
        if not np.isfinite(val):
            continue
        timestamps.append(np.datetime64(ts, 's'))
        values.append(val)
    if not timestamps:
        raise ValueError('No valid data rows found in .ggp content.')
    return np.asarray(timestamps, dtype='datetime64[s]'), np.asarray(values, dtype=np.float64)


def _gap_report(raw_timestamps: np.ndarray) -> dict[str, Any]:
    timestamps = np.asarray(raw_timestamps)
    finite_mask = _finite_time_mask(timestamps)
    times_clean = timestamps[finite_mask].astype('datetime64[s]')
    if len(times_clean) < 2:
        return {
            'n_samples_total': int(len(times_clean)),
            'median_dt_s': None,
            'gap_count': 0,
            'duplicate_count': 0,
            'reverse_count': 0,
            'missing_samples_estimate': 0,
            'segment_count': 1 if len(times_clean) else 0,
            'largest_contiguous_segment_samples': int(len(times_clean)),
        }

    reverse_count = int(np.sum(np.diff(times_clean) < np.timedelta64(0, 's'))) if len(times_clean) > 1 else 0
    timestamps_sorted = np.sort(times_clean)
    dt = np.diff(timestamps_sorted).astype('timedelta64[s]').astype(np.int64)
    positive = dt[dt > 0]
    median_dt = int(np.median(positive)) if len(positive) else None
    duplicate_count = int(np.sum(dt == 0))
    if median_dt is None or median_dt <= 0:
        gap_count = 0
        missing_samples = 0
        segment_count = 1
        largest = len(timestamps_sorted)
    else:
        gap_steps = np.rint(dt / median_dt).astype(np.int64)
        gap_mask = gap_steps > 1
        gap_count = int(np.sum(gap_mask))
        missing_samples = int(np.sum(np.maximum(gap_steps[gap_mask] - 1, 0)))
        segment_breaks = np.where((dt != median_dt) | (dt <= 0))[0]
        segment_count = int(len(segment_breaks) + 1)
        boundaries = np.concatenate(([0], segment_breaks + 1, [len(timestamps_sorted)]))
        lengths = np.diff(boundaries)
        largest = int(np.max(lengths)) if len(lengths) else 0
    return {
        'n_samples_total': int(len(times_clean)),
        'median_dt_s': median_dt,
        'gap_count': gap_count,
        'duplicate_count': duplicate_count,
        'reverse_count': reverse_count,
        'missing_samples_estimate': missing_samples,
        'segment_count': segment_count,
        'largest_contiguous_segment_samples': largest,
    }


def _select_longest_contiguous_segment(timestamps: np.ndarray, values: np.ndarray, expected_dt_s: int | None) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if len(timestamps) == 0:
        raise ValueError('Empty time series.')
    if expected_dt_s is None or len(timestamps) < 2:
        return timestamps, values, {
            'strategy': 'entire_series',
            'segment_index': 0,
            'segment_start': str(timestamps[0]),
            'segment_end': str(timestamps[-1]),
            'segment_samples': int(len(timestamps)),
        }
    dt = np.diff(timestamps).astype('timedelta64[s]').astype(np.int64)
    breaks = np.where((dt != expected_dt_s) | (dt <= 0))[0]
    boundaries = np.concatenate(([0], breaks + 1, [len(timestamps)]))
    best_i = 0
    best_len = -1
    segments = []
    for i in range(len(boundaries) - 1):
        s = int(boundaries[i]); e = int(boundaries[i + 1]); seg_len = e - s
        segments.append((s, e, seg_len))
        if seg_len > best_len:
            best_len = seg_len; best_i = i
    s, e, seg_len = segments[best_i]
    return timestamps[s:e], values[s:e], {
        'strategy': 'longest_contiguous_segment',
        'segment_index': int(best_i),
        'segment_start': str(timestamps[s]),
        'segment_end': str(timestamps[e - 1]),
        'segment_samples': int(seg_len),
    }


def _parse_csv_series(text: str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    timestamps: list[np.datetime64] = []
    values: list[float] = []
    meta: dict[str, Any] = {'dropped_rows': 0}
    for row in reader:
        ts_raw = (row.get('timestamp') or row.get('time') or '').strip()
        val_raw = (row.get('gravity_residual') or row.get('value') or row.get('gravity') or '').strip()
        if not ts_raw or not val_raw:
            meta['dropped_rows'] += 1
            continue
        try:
            ts = np.datetime64(ts_raw)
            val = float(val_raw)
        except Exception:
            logger.exception('CSV row parsing failed')
            meta['dropped_rows'] += 1
            continue
        if not np.isfinite(val):
            meta['dropped_rows'] += 1
            continue
        timestamps.append(ts.astype('datetime64[s]'))
        values.append(val)
        if row.get('station_code') and 'station_code' not in meta:
            meta['station_code'] = row['station_code']
        if row.get('longitude') and 'longitude_deg' not in meta:
            try:
                meta['longitude_deg'] = float(row['longitude'])
            except ValueError:
                logger.exception('Longitude metadata parsing failed')
        if row.get('latitude') and 'latitude_deg' not in meta:
            try:
                meta['latitude_deg'] = float(row['latitude'])
            except ValueError:
                logger.exception('Latitude metadata parsing failed')
        if row.get('units') and 'units' not in meta:
            meta['units'] = row['units']
    if not timestamps:
        raise ValueError('No valid timestamp/value rows found in CSV.')
    t_arr = np.asarray(timestamps, dtype='datetime64[s]')
    v_arr = np.asarray(values, dtype=np.float64)
    finite_mask = _finite_time_mask(t_arr) & np.isfinite(v_arr)
    t_arr = t_arr[finite_mask]
    v_arr = v_arr[finite_mask]
    return t_arr, v_arr, meta


def _unit_validation(values: np.ndarray, declared_units: str | None = None) -> list[str]:
    warnings: list[str] = []
    if declared_units:
        normalized = declared_units.strip().lower()
        known = {'ugal', 'µgal', 'm/s^2', 'ms^-2', 'nm/s^2', 'gravity residual (dataset units)'}
        if normalized not in known:
            warnings.append(f'Unrecognized declared units: {declared_units}')
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        warnings.append('No finite values available for unit sanity checks.')
        return warnings
    vmax = float(np.max(np.abs(finite)))
    if vmax > 1e6:
        warnings.append('Gravity values are extremely large; check unit normalization or malformed parsing.')
    return warnings


def load_real_gravity_dataset(
    *,
    source_path: str | Path,
    station_code: str | None = None,
    metadata_path: str | Path | None = None,
    segment_strategy: str = 'longest_contiguous',
) -> dict[str, Any]:
    path = Path(source_path)
    source_kind = path.suffix.lower().lstrip('.') if path.is_file() else 'directory'

    if metadata_path is not None:
        metadata_text = Path(metadata_path).read_text(encoding='utf-8', errors='ignore')
    else:
        metadata_text, _ = _find_metadata_text(path)
    station_meta = parse_station_metadata(metadata_text or '')

    csv_meta: dict[str, Any] = {}
    if path.suffix.lower() == '.csv':
        timestamps_raw, values_raw, csv_meta = _parse_csv_series(path.read_text(encoding='utf-8', errors='ignore'))
        code = station_code or csv_meta.get('station_code') or path.stem
    else:
        if path.suffix.lower() == '.ggp':
            code = station_code or path.stem
            text = path.read_text(encoding='utf-8', errors='ignore')
        elif path.suffix.lower() == '.zip':
            if not station_code:
                stations = list_stations_in_source(path)
                if not stations:
                    raise ValueError('No .ggp stations found in zip archive.')
                code = str(stations[0]['station_code'])
            else:
                code = station_code
            member_name = None
            with zipfile.ZipFile(path, 'r') as zf:
                for name in zf.namelist():
                    if name.lower().endswith(f'/{code.lower()}.ggp') or Path(name).name.lower() == f'{code.lower()}.ggp':
                        member_name = name
                        break
            if member_name is None:
                raise FileNotFoundError(f'Station {code} not found in archive {path.name}.')
            text = _read_text_from_source(path, member_name=member_name)
        elif path.is_dir():
            if not station_code:
                stations = list_stations_in_source(path)
                if not stations:
                    raise ValueError('No .ggp stations found in directory.')
                code = str(stations[0]['station_code'])
            else:
                code = station_code
            ggp_path = path / f'{code}.ggp'
            if not ggp_path.exists():
                raise FileNotFoundError(f'Station file not found: {ggp_path}')
            text = ggp_path.read_text(encoding='utf-8', errors='ignore')
        else:
            raise ValueError(f'Unsupported gravimetry source: {path}')
        timestamps_raw, values_raw = parse_ggp_lines(text.splitlines())

    if len(timestamps_raw) != len(values_raw):
        raise ValueError('Timestamp/value arrays have inconsistent lengths.')

    timestamps_raw = np.asarray(timestamps_raw)
    values_raw = np.asarray(values_raw, dtype=np.float64)
    finite_mask = _finite_time_mask(timestamps_raw) & np.isfinite(values_raw)
    timestamps_raw = timestamps_raw[finite_mask]
    values_raw = values_raw[finite_mask]
    gap_report = _gap_report(timestamps_raw)
    order = np.argsort(timestamps_raw)
    timestamps = timestamps_raw[order]
    values = values_raw[order]

    finite_mask = _finite_time_mask(timestamps) & np.isfinite(values)
    timestamps = timestamps[finite_mask]
    values = values[finite_mask]

    expected_dt_s = gap_report.get('median_dt_s')
    if segment_strategy == 'longest_contiguous':
        seg_t, seg_v, segment_report = _select_longest_contiguous_segment(timestamps, values, expected_dt_s)
    else:
        seg_t, seg_v = timestamps, values
        segment_report = {
            'strategy': 'entire_series',
            'segment_index': 0,
            'segment_start': str(timestamps[0]),
            'segment_end': str(timestamps[-1]),
            'segment_samples': int(len(timestamps)),
        }

    diffs = np.diff(seg_t).astype('timedelta64[s]').astype(np.int64)
    diffs = diffs[diffs > 0]
    if len(diffs) == 0:
        raise ValueError('Cannot infer sampling rate')
    dt = float(np.median(diffs))
    if dt <= 0:
        raise ValueError('Unable to infer positive sampling interval from selected segment.')
    sample_rate_hz = float(1.0 / dt)
    t = (seg_t - seg_t[0]).astype('timedelta64[s]').astype(np.float64)
    t_full = (timestamps - timestamps[0]).astype('timedelta64[s]').astype(np.float64)

    info = station_meta.get(code, StationInfo(code=code))
    longitude = csv_meta.get('longitude_deg', info.longitude_deg)
    latitude = csv_meta.get('latitude_deg', info.latitude_deg)
    declared_units = csv_meta.get('units')
    unit_warnings = _unit_validation(values, declared_units)

    return {
        't': t,
        'gravity_residual': seg_v.astype(np.float64),
        'timestamps': seg_t,
        'timestamps_full': timestamps,
        't_full': t_full,
        'gravity_residual_full': values.astype(np.float64),
        'sample_rate_hz': sample_rate_hz,
        'station_code': code,
        'longitude_deg': longitude,
        'latitude_deg': latitude,
        'units': declared_units or 'gravity residual (dataset units)',
        'source_path': str(path),
        'source_kind': source_kind,
        'gap_report': gap_report,
        'analysis_segment': segment_report,
        'record_start': str(timestamps[0]),
        'record_end': str(timestamps[-1]),
        'unit_warnings': unit_warnings,
        'dropped_rows': int(csv_meta.get('dropped_rows', 0)),
    }


def convert_ggp_to_csv(
    *,
    source_path: str | Path,
    output_path: str | Path,
    station_code: str | None = None,
    metadata_path: str | Path | None = None,
) -> Path:
    data = load_real_gravity_dataset(
        source_path=source_path,
        station_code=station_code,
        metadata_path=metadata_path,
        segment_strategy='entire_series',
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'gravity_residual', 'station_code', 'longitude', 'latitude', 'units'])
        lon = '' if data.get('longitude_deg') is None else data.get('longitude_deg')
        lat = '' if data.get('latitude_deg') is None else data.get('latitude_deg')
        units = data.get('units', 'gravity residual (dataset units)')
        for ts, val in zip(data['timestamps_full'], data['gravity_residual_full']):
            writer.writerow([str(ts).replace('T', ' '), f'{float(val):.12g}', data['station_code'], lon, lat, units])
    return out
