export type ParserMetadata = {
  name: string;
  bank_label: string;
  display_name: string;
  institution: string;
  statement_type: string;
  country: string;
  supports_password: boolean;
};

export type Direction = "DEBIT" | "CREDIT";

/**
 * Amount-bearing fields are serialized as fixed-decimal strings (e.g. "12345.00")
 * to avoid floating-point precision loss. Convert with `Number(amount)` only when
 * doing arithmetic; for display, prefer `formatMoney` in StatementSummary.
 */
export type Transaction = {
  txn_date: string;
  post_date: string;
  description: string;
  amount: string;
  direction: Direction;
  card_last4: string;
  cardholder: string;
  source_file: string;
};

export type StatementParseResponse = {
  parser_name: string;
  bank_label: string;
  statement_date: string;
  period: string;
  transaction_count: number;
  totals: {
    debit: string;
    credit: string;
    net: string;
  };
  transactions: Transaction[];
  meta: Record<string, string>;
};

export type ApiError = {
  error: string;
  message: string;
};
