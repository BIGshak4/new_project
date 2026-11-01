"""Strict comma/double-quote CSV reader without the csv module.

Input is an iterable of text chunks, not necessarily lines. CRLF and LF end
records outside quotes; a bare CR outside quotes is rejected. Embedded CR/LF
inside quoted fields is preserved. Quotes only begin an empty field; after a
closing quote only comma, record end, or EOF is valid. No implicit trimming,
header conversion or type coercion. Empty input produces no records.
"""


def iter_csv_rows(chunks):
    state, pending_cr = 'start', False
    field, row = [], []
    record_started = False
    for chunk in chunks:
        if not isinstance(chunk, str):
            raise TypeError('text chunks required')
        for char in chunk:
            if pending_cr:
                if char != '\n':
                    raise ValueError('bare CR outside quoted field')
                pending_cr = False
                yield row
                row, field, state = [], [], 'start'
                record_started = False
                continue
            if state == 'quoted':
                if char == '"':
                    state = 'after_quote'
                else:
                    field.append(char)
                continue
            if state == 'after_quote' and char == '"':
                field.append('"')
                state = 'quoted'
                continue
            if char == ',':
                row.append(''.join(field))
                field, state = [], 'start'
                record_started = True
            elif char in '\r\n':
                row.append(''.join(field))
                field = []
                if char == '\r':
                    pending_cr = True
                else:
                    yield row
                    row, state = [], 'start'
                    record_started = False
            elif char == '"':
                if state != 'start':
                    raise ValueError('quote inside unquoted field')
                state = 'quoted'
                record_started = True
            else:
                if state == 'after_quote':
                    raise ValueError('unexpected character after closing quote')
                field.append(char)
                state = 'plain'
                record_started = True
    if pending_cr:
        raise ValueError('bare CR at EOF')
    if state == 'quoted':
        raise ValueError('unterminated quoted field')
    if record_started:
        row.append(''.join(field))
        yield row


def read_csv_file(path, chunk_size=4096):
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError('positive chunk size required')
    with open(path, encoding='utf-8', newline='') as source:
        yield from iter_csv_rows(iter(lambda: source.read(chunk_size), ''))


def parse_csv(text):
    """Execution adapter materializes output; core parser yields one row."""
    return list(iter_csv_rows([text]))
