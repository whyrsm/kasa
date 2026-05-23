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

export type Transaction = {
  txn_date: string;
  post_date: string;
  description: string;
  amount: number;
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
    debit: number;
    credit: number;
    net: number;
  };
  transactions: Transaction[];
  meta: Record<string, string>;
};

export type ApiError = {
  error: string;
  message: string;
};
