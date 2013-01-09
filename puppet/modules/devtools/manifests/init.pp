class devtools {
    package { ['gcc', 'curl', ]:
        ensure => installed,
    }
}