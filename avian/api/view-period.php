<?php
declare(strict_types=1);

/** Detection timestamps are station-local wall time, as stored by BirdNET. */
function viewPeriod(int $hours, bool $overnight, ?DateTimeImmutable $now = null): array {
    $zone = new DateTimeZone('America/Los_Angeles');
    $now = ($now ?? new DateTimeImmutable('now', $zone))->setTimezone($zone);
    $end = $now;
    $start = $now->modify('-' . $hours . ' hours');
    if ($overnight) {
        // Grants Pass, Oregon. Compute each calendar day's solar events so
        // seasonal changes and Pacific daylight-saving transitions are handled.
        $day = $now->setTime(12, 0);
        $sun = date_sun_info($day->getTimestamp(), 42.439, -123.328);
        if ($now->getTimestamp() < $sun['sunset'] + 3600) {
            $day = $day->modify('-1 day');
            $sun = date_sun_info($day->getTimestamp(), 42.439, -123.328);
        }
        $next = date_sun_info($day->modify('+1 day')->getTimestamp(), 42.439, -123.328);
        $start = (new DateTimeImmutable('@' . ($sun['sunset'] + 3600)))->setTimezone($zone);
        $end = (new DateTimeImmutable('@' . min($now->getTimestamp(), $next['sunrise'] - 3600)))->setTimezone($zone);
    }
    $days = $hours === 168 ? 60 : 10;
    return ['start' => $start->format('Y-m-d H:i:s'),
            'end' => $end->format('Y-m-d H:i:s'),
            'lookback_start' => $start->modify('-' . $days . ' days')->format('Y-m-d H:i:s'),
            'lookback_days' => $days, 'timezone' => $zone->getName()];
}
