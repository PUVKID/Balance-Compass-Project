use std::io::{self, Read};

// 공식 자료의 만원 문자열을 부동소수점 없이 정확한 원 정수로 바꾼다.
fn normalize(raw: &str) -> Result<i64, String> {
    let raw = raw.trim();
    let parts: Vec<&str> = raw.split('.').collect();
    if parts.len() > 2 || parts[0].is_empty() { return Err("금액 형식 오류".into()); }
    let groups: Vec<&str> = parts[0].split(',').collect();
    if groups.iter().any(|g| g.is_empty() || !g.bytes().all(|c| c.is_ascii_digit())) {
        return Err("금액에는 양의 숫자와 올바른 쉼표만 허용됩니다".into());
    }
    if groups.len() > 1 && (groups[0].len() > 3 || groups.iter().skip(1).any(|g| g.len() != 3)) {
        return Err("금액 쉼표 위치 오류".into());
    }
    let whole: i64 = groups.concat().parse().map_err(|_| "정수 범위 초과")?;
    let fraction = if parts.len() == 2 {
        let f = parts[1];
        if f.is_empty() || f.len() > 4 || !f.bytes().all(|c| c.is_ascii_digit()) { return Err("만원 소수는 네 자리까지 허용됩니다".into()); }
        f.parse::<i64>().map_err(|_| "소수 형식 오류")? * 10_i64.pow(4 - f.len() as u32)
    } else { 0 };
    whole.checked_mul(10_000).and_then(|w| w.checked_add(fraction)).ok_or_else(|| "원 단위 정수 범위 초과".into())
}

fn main() {
    if std::env::args().len() != 1 { eprintln!("사용법: bc-money < 만원금액_줄별입력"); std::process::exit(2); }
    let mut input = String::new();
    if io::stdin().read_to_string(&mut input).is_err() { eprintln!("UTF-8 입력을 읽을 수 없습니다"); std::process::exit(2); }
    let mut values = Vec::new();
    for (i, line) in input.lines().enumerate() {
        match normalize(line) {
            Ok(n) => values.push(n.to_string()),
            Err(e) => { eprintln!("{}행: {}", i + 1, e); std::process::exit(2); }
        }
    }
    // 전체 입력 검증 후에만 출력해 실패 시 부분 결과의 오용을 막는다.
    if !values.is_empty() { println!("{}", values.join("\n")); }
}

#[cfg(test)]
mod tests {
    use super::normalize;
    #[test] fn exact_won() { assert_eq!(normalize("12,345.6789"), Ok(123456789)); assert_eq!(normalize("0"),Ok(0)); }
    #[test] fn rejects_bad_grouping() { for x in ["1,23", "1,,000", "12,3456", "-1", "NaN", "", "1e4", "1.00001"] { assert!(normalize(x).is_err(), "{x}"); } }
    #[test] fn overflow() { assert!(normalize("9223372036854775807").is_err()); }
    #[test] fn leading_zero_and_spaces() { assert_eq!(normalize(" 001.5 "), Ok(15000)); }
}
