from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    identifier: str
    category: str
    keywords: tuple[str, ...]
    explanation: str
    verification: str


RULES = (
    Rule(
        "NGINX_PORT_CONFLICT", "network", ("address already in use", "bind()"),
        "Port başka bir süreç tarafından kullanılıyor olabilir.",
        "sudo ss -ltnp '( sport = :80 )'",
    ),
    Rule(
        "NGINX_CONFIG_ERROR", "configuration", ("unknown directive",),
        "Nginx yapılandırmasında tanınmayan bir direktif bulunuyor.",
        "sudo nginx -t",
    ),
    Rule(
        "DNS_RESOLUTION_ERROR", "dns", ("temporary failure in name resolution",),
        "İsim çözümleme başarısız olmuş. DNS veya hosts kaydını kontrol edin.",
        "getent hosts example.internal && cat /etc/resolv.conf",
    ),
    Rule(
        "DISK_FULL", "storage", ("no space left on device",),
        "Dosya sisteminde kullanılabilir alan kalmamış olabilir.",
        "df -h && df -i",
    ),
    Rule(
        "PERMISSION_DENIED", "permissions", ("permission denied",),
        "İşlem için gerekli dosya veya servis izni eksik olabilir.",
        "id && ls -l /path/to/resource",
    ),
)
