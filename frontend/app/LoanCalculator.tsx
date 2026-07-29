"use client";

import { useEffect, useMemo, useState } from "react";

type LoanCalculatorProps = {
  propertyPrice: number;
  annualPropertyTax: number | null;
  propertyState: string;
  propertyCounty: string;
};

type StateOption = {
  fips: string;
  code: string;
  name: string;
};

type CountyOption = {
  fips: string;
  name: string;
};

type LoanProgram = "conventional" | "fha";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

function currency(value: number) {
  if (!Number.isFinite(value)) return "$0";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Math.max(0, value));
}

function paymentFactor(annualRate: number, termYears: number) {
  const payments = Math.max(1, Math.round(termYears * 12));
  const monthlyRate = Math.max(0, annualRate) / 1200;
  if (monthlyRate === 0) return 1 / payments;
  const growth = Math.pow(1 + monthlyRate, payments);
  return (monthlyRate * growth) / (growth - 1);
}

function NumericField({
  label,
  value,
  onChange,
  suffix,
  step = "any",
  format = "number",
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  suffix?: string;
  step?: string;
  format?: "currency" | "number";
}) {
  const [isFocused, setIsFocused] = useState(false);
  const isCurrency = format === "currency";

  return (
    <label style={{ display: "grid", gap: 7 }}>
      <span
        style={{
          color: "rgba(255,255,255,0.58)",
          fontSize: 12,
          fontWeight: 800,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
        }}
      >
        {label}
      </span>
      <div style={{ position: "relative" }}>
        <input
          type={isCurrency ? "text" : "number"}
          inputMode={isCurrency ? "decimal" : undefined}
          min={isCurrency ? undefined : "0"}
          step={isCurrency ? undefined : step}
          value={isCurrency && !isFocused ? currency(value) : value}
          onFocus={(event) => {
            setIsFocused(true);
            if (isCurrency) event.currentTarget.select();
          }}
          onClick={(event) => {
            if (isCurrency) event.currentTarget.select();
          }}
          onBlur={() => setIsFocused(false)}
          onChange={(event) => {
            const rawValue = isCurrency
              ? event.target.value.replace(/[^0-9.]/g, "")
              : event.target.value;
            onChange(Math.max(0, Number(rawValue) || 0));
          }}
          style={{
            width: "100%",
            borderRadius: 14,
            border: "1px solid rgba(255,255,255,0.10)",
            background: "rgba(0,0,0,0.34)",
            color: "#fff",
            padding: suffix ? "13px 48px 13px 14px" : "13px 14px",
            fontSize: 15,
            outline: "none",
          }}
        />
        {suffix ? (
          <span
            style={{
              position: "absolute",
              right: 14,
              top: "50%",
              transform: "translateY(-50%)",
              color: "rgba(255,255,255,0.45)",
              fontSize: 13,
              pointerEvents: "none",
            }}
          >
            {suffix}
          </span>
        ) : null}
      </div>
    </label>
  );
}

function ResultCard({
  label,
  value,
  detail,
  accent,
}: {
  label: string;
  value: string;
  detail?: string;
  accent?: string;
}) {
  return (
    <div
      style={{
        borderRadius: 18,
        border: "1px solid rgba(255,255,255,0.10)",
        background: "rgba(0,0,0,0.28)",
        padding: 16,
      }}
    >
      <div
        style={{
          color: "rgba(255,255,255,0.54)",
          fontSize: 11,
          fontWeight: 800,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
        }}
      >
        {label}
      </div>
      <div
        style={{
          marginTop: 7,
          color: accent || "#fff",
          fontSize: 22,
          fontWeight: 900,
          letterSpacing: "-0.03em",
        }}
      >
        {value}
      </div>
      {detail ? (
        <div
          style={{
            marginTop: 6,
            color: "rgba(255,255,255,0.48)",
            fontSize: 12,
            lineHeight: 1.5,
          }}
        >
          {detail}
        </div>
      ) : null}
    </div>
  );
}

export default function LoanCalculator({
  propertyPrice,
  annualPropertyTax,
  propertyState,
  propertyCounty,
}: LoanCalculatorProps) {
  const [purchasePrice, setPurchasePrice] = useState(propertyPrice || 400000);
  const [annualIncome, setAnnualIncome] = useState(100000);
  const [monthlyDebts, setMonthlyDebts] = useState(750);
  const [downPaymentPercent, setDownPaymentPercent] = useState(10);
  const [interestRate, setInterestRate] = useState(6.75);
  const [termYears, setTermYears] = useState(30);
  const [annualTaxes, setAnnualTaxes] = useState(annualPropertyTax || 4800);
  const [annualInsurance, setAnnualInsurance] = useState(1800);
  const [monthlyHoa, setMonthlyHoa] = useState(0);
  const [annualMortgageInsuranceRate, setAnnualMortgageInsuranceRate] =
    useState(0.5);
  const [financedUpfrontFeePercent, setFinancedUpfrontFeePercent] =
    useState(0);
  const [closingCostPercent, setClosingCostPercent] = useState(3);
  const [targetDti, setTargetDti] = useState(43);
  const [loanProgram, setLoanProgram] =
    useState<LoanProgram>("conventional");
  const [states, setStates] = useState<StateOption[]>([]);
  const [counties, setCounties] = useState<CountyOption[]>([]);
  const [stateFips, setStateFips] = useState("");
  const [countyFips, setCountyFips] = useState("");
  const [estimateLoading, setEstimateLoading] = useState(false);
  const [estimateError, setEstimateError] = useState("");
  const [taxSource, setTaxSource] = useState(
    annualPropertyTax
      ? "Reported property tax from the selected property"
      : "Manual estimate"
  );
  const [insuranceSource, setInsuranceSource] = useState(
    "Manual planning estimate"
  );
  const [interestRateSource, setInterestRateSource] = useState(
    "Manual planning assumption"
  );
  const [interestRateLoading, setInterestRateLoading] = useState(true);

  useEffect(() => {
    if (propertyPrice > 0) setPurchasePrice(propertyPrice);
  }, [propertyPrice]);

  useEffect(() => {
    if (annualPropertyTax && annualPropertyTax > 0) {
      setAnnualTaxes(annualPropertyTax);
      setTaxSource("Reported property tax from the selected property");
    }
  }, [annualPropertyTax]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE_URL}/affordability/mortgage-rate`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Mortgage-rate benchmark unavailable");
        }
        return data;
      })
      .then((data) => {
        if (cancelled) return;
        const benchmarkRate = Number(data.rate_percent);
        if (benchmarkRate > 0) {
          setInterestRate(benchmarkRate);
          setInterestRateSource(
            `${data.source} · ${data.observation_date} · national 30-year benchmark`
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          setInterestRateSource(
            "Live benchmark unavailable · editable 6.75% fallback"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setInterestRateLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE_URL}/affordability/states`)
      .then((response) => {
        if (!response.ok) throw new Error("State directory unavailable");
        return response.json();
      })
      .then((data) => {
        if (cancelled) return;
        const options = Array.isArray(data.states) ? data.states : [];
        setStates(options);
        const normalizedState = propertyState.trim().toLowerCase();
        const matched = options.find(
          (option: StateOption) =>
            option.code.toLowerCase() === normalizedState ||
            option.name.toLowerCase() === normalizedState
        );
        if (matched) setStateFips(matched.fips);
      })
      .catch(() => {
        if (!cancelled) setEstimateError("Unable to load states.");
      });
    return () => {
      cancelled = true;
    };
  }, [propertyState]);

  useEffect(() => {
    if (!stateFips) {
      setCounties([]);
      setCountyFips("");
      return;
    }
    let cancelled = false;
    setEstimateError("");
    fetch(`${API_BASE_URL}/affordability/counties?state=${stateFips}`)
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "County directory unavailable");
        }
        return data;
      })
      .then((data) => {
        if (cancelled) return;
        const options = Array.isArray(data.counties) ? data.counties : [];
        setCounties(options);
        const normalizedCounty = propertyCounty
          .replace(/\s+county$/i, "")
          .trim()
          .toLowerCase();
        const matched = options.find(
          (option: CountyOption) =>
            option.name
              .replace(/\s+county$/i, "")
              .trim()
              .toLowerCase() === normalizedCounty
        );
        setCountyFips(matched?.fips || "");
      })
      .catch((error) => {
        if (!cancelled) {
          setEstimateError(
            error instanceof Error ? error.message : "Unable to load counties."
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [propertyCounty, stateFips]);

  async function applyLocationEstimates() {
    if (!stateFips || !countyFips || purchasePrice <= 0) {
      setEstimateError("Select a state and county and enter a purchase price.");
      return;
    }
    setEstimateLoading(true);
    setEstimateError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/affordability/estimate?state=${stateFips}&county=${countyFips}&purchase_price=${purchasePrice}`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Location estimate unavailable");
      }
      const tax = Number(data?.property_tax?.annual_estimate) || 0;
      const insurance =
        Number(data?.homeowners_insurance?.annual_estimate) || 0;
      if (tax > 0) setAnnualTaxes(tax);
      if (insurance > 0) setAnnualInsurance(insurance);
      setTaxSource(
        `${data.property_tax.source} · ${Number(
          data.property_tax.effective_rate_percent
        ).toFixed(3)}% effective rate`
      );
      setInsuranceSource(
        `${data.homeowners_insurance.source} · ${Number(
          data.homeowners_insurance.planning_rate_percent
        ).toFixed(3)}% planning rate`
      );
    } catch (error) {
      setEstimateError(
        error instanceof Error ? error.message : "Unable to calculate estimate"
      );
    } finally {
      setEstimateLoading(false);
    }
  }

  function resetToPropertyData() {
    if (propertyPrice > 0) setPurchasePrice(propertyPrice);
    if (annualPropertyTax && annualPropertyTax > 0) {
      setAnnualTaxes(annualPropertyTax);
      setTaxSource("Reported property tax from the selected property");
    }
    setAnnualInsurance(1800);
    setInsuranceSource("Manual planning estimate");
    setEstimateError("");
  }

  function applyLoanProgram(program: LoanProgram) {
    setLoanProgram(program);
    if (program === "fha") {
      setDownPaymentPercent(3.5);
      setAnnualMortgageInsuranceRate(0.55);
      setFinancedUpfrontFeePercent(1.75);
      return;
    }
    setDownPaymentPercent(10);
    setAnnualMortgageInsuranceRate(0.5);
    setFinancedUpfrontFeePercent(0);
  }

  const result = useMemo(() => {
    const downPayment = purchasePrice * (downPaymentPercent / 100);
    const baseLoanAmount = Math.max(0, purchasePrice - downPayment);
    const financedUpfrontFee =
      baseLoanAmount * (financedUpfrontFeePercent / 100);
    const totalLoanAmount = baseLoanAmount + financedUpfrontFee;
    const factor = paymentFactor(interestRate, termYears);
    const principalAndInterest = totalLoanAmount * factor;
    const monthlyTax = annualTaxes / 12;
    const monthlyInsurance = annualInsurance / 12;
    const monthlyMortgageInsurance =
      baseLoanAmount * (annualMortgageInsuranceRate / 100) / 12;
    const totalHousingPayment =
      principalAndInterest +
      monthlyTax +
      monthlyInsurance +
      monthlyMortgageInsurance +
      monthlyHoa;
    const grossMonthlyIncome = annualIncome / 12;
    const housingDti =
      grossMonthlyIncome > 0
        ? (totalHousingPayment / grossMonthlyIncome) * 100
        : 0;
    const totalDti =
      grossMonthlyIncome > 0
        ? ((totalHousingPayment + monthlyDebts) / grossMonthlyIncome) * 100
        : 0;
    const maximumTotalDebt = grossMonthlyIncome * (targetDti / 100);
    const maximumHousingPayment = Math.max(
      0,
      maximumTotalDebt - monthlyDebts
    );
    const amountAvailableForPrincipalInterestAndMi = Math.max(
      0,
      maximumHousingPayment -
        monthlyTax -
        monthlyInsurance -
        monthlyHoa
    );
    const monthlyMiFactor = annualMortgageInsuranceRate / 100 / 12;
    const baseLoanShare = 1 + financedUpfrontFeePercent / 100;
    const baseLoanPaymentFactor =
      factor * baseLoanShare + monthlyMiFactor;
    const financedShare = Math.max(0.01, 1 - downPaymentPercent / 100);
    const maximumPurchasePriceForDti = (dtiPercent: number) => {
      const housingAllowance = Math.max(
        0,
        grossMonthlyIncome * (dtiPercent / 100) - monthlyDebts
      );
      const amountForLoanAndMi = Math.max(
        0,
        housingAllowance -
          monthlyTax -
          monthlyInsurance -
          monthlyHoa
      );
      const baseLoan =
        baseLoanPaymentFactor > 0
          ? amountForLoanAndMi / baseLoanPaymentFactor
          : 0;
      return baseLoan / financedShare;
    };
    const conservativeDti = Math.min(36, targetDti);
    const conservativePurchasePrice =
      maximumPurchasePriceForDti(conservativeDti);
    const maximumPurchasePrice =
      maximumPurchasePriceForDti(targetDti);
    const estimatedCashToClose =
      downPayment + purchasePrice * (closingCostPercent / 100);

    return {
      downPayment,
      totalLoanAmount,
      financedUpfrontFee,
      principalAndInterest,
      monthlyTax,
      monthlyInsurance,
      monthlyMortgageInsurance,
      totalHousingPayment,
      housingDti,
      totalDti,
      maximumHousingPayment,
      maximumPurchasePrice,
      conservativeDti,
      conservativePurchasePrice,
      estimatedCashToClose,
      withinTarget:
        grossMonthlyIncome > 0 &&
        totalHousingPayment + monthlyDebts <= maximumTotalDebt,
    };
  }, [
    annualIncome,
    annualInsurance,
    annualMortgageInsuranceRate,
    annualTaxes,
    closingCostPercent,
    downPaymentPercent,
    financedUpfrontFeePercent,
    interestRate,
    monthlyDebts,
    monthlyHoa,
    purchasePrice,
    targetDti,
    termYears,
  ]);

  return (
    <section
      style={{
        borderRadius: 28,
        border: "1px solid rgba(255,255,255,0.10)",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04))",
        boxShadow: "0 24px 80px rgba(0,0,0,0.35)",
        backdropFilter: "blur(18px)",
        padding: 22,
      }}
    >
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 22, fontWeight: 900, letterSpacing: "-0.03em" }}>
          Affordability & Loan Estimate
        </div>
        <div
          style={{
            marginTop: 7,
            color: "rgba(255,255,255,0.55)",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          Uses standard amortization and debt-to-income calculations. Enter the
          actual lender-provided rate, mortgage insurance, fees, and DTI target
          for the most meaningful estimate.
        </div>
      </div>

      <div
        style={{
          marginBottom: 18,
          borderRadius: 20,
          border: "1px solid rgba(139,92,246,0.24)",
          background: "rgba(139,92,246,0.07)",
          padding: 16,
        }}
      >
        <label style={{ display: "grid", gap: 7, maxWidth: 420 }}>
          <span
            style={{
              color: "rgba(255,255,255,0.58)",
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: "0.04em",
              textTransform: "uppercase",
            }}
          >
            Loan program
          </span>
          <select
            aria-label="Loan program"
            value={loanProgram}
            onChange={(event) =>
              applyLoanProgram(event.target.value as LoanProgram)
            }
            style={{
              width: "100%",
              borderRadius: 14,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "#10131f",
              color: "#fff",
              padding: "13px 14px",
              fontSize: 15,
              fontWeight: 800,
              outline: "none",
            }}
          >
            <option value="conventional">Conventional</option>
            <option value="fha">FHA</option>
          </select>
        </label>
        <div
          style={{
            marginTop: 11,
            color: "rgba(255,255,255,0.56)",
            fontSize: 12,
            lineHeight: 1.6,
          }}
        >
          {loanProgram === "fha"
            ? "FHA starting assumptions: 3.5% down, 1.75% financed upfront MIP, and 0.55% annual MIP for a common 30-year, greater-than-95% LTV scenario. FHA loan limits and the exact annual MIP can vary."
            : "Conventional starting assumptions: 10% down, no financed upfront mortgage-insurance fee, and a 0.50% PMI planning rate. Set mortgage insurance to 0% when it is not required; an actual PMI quote depends heavily on credit and LTV."}
        </div>
      </div>

      <div
        style={{
          marginBottom: 22,
          borderRadius: 20,
          border: "1px solid rgba(34,211,238,0.20)",
          background: "rgba(34,211,238,0.06)",
          padding: 16,
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 900 }}>
          Automatic tax & insurance estimates
        </div>
        <div
          style={{
            marginTop: 5,
            color: "rgba(255,255,255,0.52)",
            fontSize: 12,
            lineHeight: 1.55,
          }}
        >
          Select the property location and apply estimates based on county tax
          statistics and a state-level insurance planning rate.
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 12,
            marginTop: 14,
          }}
        >
          <label style={{ display: "grid", gap: 7 }}>
            <span
              style={{
                color: "rgba(255,255,255,0.58)",
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              State
            </span>
            <select
              aria-label="State"
              value={stateFips}
              onChange={(event) => {
                setStateFips(event.target.value);
                setCountyFips("");
              }}
              style={{
                width: "100%",
                borderRadius: 14,
                border: "1px solid rgba(255,255,255,0.10)",
                background: "#10131f",
                color: "#fff",
                padding: "13px 14px",
                fontSize: 15,
                outline: "none",
              }}
            >
              <option value="">Select a state</option>
              {states.map((state) => (
                <option key={state.fips} value={state.fips}>
                  {state.name}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 7 }}>
            <span
              style={{
                color: "rgba(255,255,255,0.58)",
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              County
            </span>
            <select
              aria-label="County"
              value={countyFips}
              disabled={!stateFips || counties.length === 0}
              onChange={(event) => setCountyFips(event.target.value)}
              style={{
                width: "100%",
                borderRadius: 14,
                border: "1px solid rgba(255,255,255,0.10)",
                background: "#10131f",
                color: "#fff",
                padding: "13px 14px",
                fontSize: 15,
                outline: "none",
                opacity: !stateFips || counties.length === 0 ? 0.55 : 1,
              }}
            >
              <option value="">
                {stateFips ? "Select a county" : "Select a state first"}
              </option>
              {counties.map((county) => (
                <option key={county.fips} value={county.fips}>
                  {county.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div
          style={{
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
            marginTop: 14,
          }}
        >
          <button
            type="button"
            onClick={applyLocationEstimates}
            disabled={estimateLoading || !stateFips || !countyFips}
            style={{
              padding: "11px 16px",
              borderRadius: 13,
              border: 0,
              background:
                estimateLoading || !stateFips || !countyFips
                  ? "rgba(255,255,255,0.16)"
                  : "#fff",
              color:
                estimateLoading || !stateFips || !countyFips
                  ? "rgba(255,255,255,0.45)"
                  : "#030712",
              fontWeight: 900,
              cursor:
                estimateLoading || !stateFips || !countyFips
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {estimateLoading ? "Calculating..." : "Use automatic estimates"}
          </button>
          <button
            type="button"
            onClick={resetToPropertyData}
            style={{
              padding: "11px 16px",
              borderRadius: 13,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.05)",
              color: "#fff",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            Reset to property data
          </button>
        </div>
        {estimateError ? (
          <div
            style={{
              marginTop: 10,
              color: "#fca5a5",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            {estimateError}
          </div>
        ) : null}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          gap: 13,
        }}
      >
        <NumericField
          label="Purchase price"
          value={purchasePrice}
          onChange={setPurchasePrice}
          format="currency"
        />
        <NumericField
          label="Gross annual income"
          value={annualIncome}
          onChange={setAnnualIncome}
          format="currency"
        />
        <NumericField
          label="Existing monthly debts"
          value={monthlyDebts}
          onChange={setMonthlyDebts}
          format="currency"
        />
        <NumericField
          label="Down payment"
          value={downPaymentPercent}
          onChange={(value) => {
            setDownPaymentPercent(value);
            if (loanProgram === "conventional") {
              setAnnualMortgageInsuranceRate((currentRate) => {
                if (value >= 20) return 0;
                return currentRate === 0 ? 0.5 : currentRate;
              });
            }
          }}
          suffix="%"
          step="0.1"
        />
        <NumericField
          label="Interest rate"
          value={interestRate}
          onChange={(value) => {
            setInterestRate(value);
            setInterestRateSource("Manually entered rate");
          }}
          suffix="%"
          step="0.01"
        />
        <NumericField
          label="Loan term"
          value={termYears}
          onChange={setTermYears}
          suffix="years"
          step="1"
        />
        <NumericField
          label="Annual property taxes"
          value={annualTaxes}
          onChange={(value) => {
            setAnnualTaxes(value);
            setTaxSource("Manual override");
          }}
          format="currency"
        />
        <NumericField
          label="Annual homeowners insurance"
          value={annualInsurance}
          onChange={(value) => {
            setAnnualInsurance(value);
            setInsuranceSource("Manual override");
          }}
          format="currency"
        />
        <NumericField
          label="Monthly HOA"
          value={monthlyHoa}
          onChange={setMonthlyHoa}
          format="currency"
        />
        <NumericField
          label="Annual mortgage insurance"
          value={annualMortgageInsuranceRate}
          onChange={setAnnualMortgageInsuranceRate}
          suffix="%"
          step="0.01"
        />
        <NumericField
          label="Financed upfront fee"
          value={financedUpfrontFeePercent}
          onChange={setFinancedUpfrontFeePercent}
          suffix="%"
          step="0.01"
        />
        <NumericField
          label="Estimated closing costs"
          value={closingCostPercent}
          onChange={setClosingCostPercent}
          suffix="%"
          step="0.1"
        />
        <NumericField
          label="Target total DTI"
          value={targetDti}
          onChange={(value) => setTargetDti(Math.min(100, value))}
          suffix="%"
          step="0.1"
        />
      </div>

      <div
        style={{
          display: "grid",
          gap: 7,
          marginTop: 12,
          color: "rgba(255,255,255,0.48)",
          fontSize: 12,
          lineHeight: 1.5,
        }}
      >
        <div>
          <strong style={{ color: "rgba(255,255,255,0.70)" }}>
            Property-tax source:
          </strong>{" "}
          {taxSource}
        </div>
        <div>
          <strong style={{ color: "rgba(255,255,255,0.70)" }}>
            Insurance source:
          </strong>{" "}
          {insuranceSource}
        </div>
        <div>
          <strong style={{ color: "rgba(255,255,255,0.70)" }}>
            Interest-rate source:
          </strong>{" "}
          {interestRateLoading
            ? "Loading current national benchmark…"
            : interestRateSource}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
          gap: 12,
          marginTop: 22,
          paddingTop: 22,
          borderTop: "1px solid rgba(255,255,255,0.10)",
        }}
      >
        <ResultCard
          label={`Estimated ${
            loanProgram === "fha" ? "FHA" : "conventional"
          } loan`}
          value={currency(result.totalLoanAmount)}
          detail={
            result.financedUpfrontFee > 0
              ? `${currency(result.financedUpfrontFee)} financed upfront fee included`
              : `${currency(result.downPayment)} down payment`
          }
        />
        <ResultCard
          label="Principal & interest"
          value={`${currency(result.principalAndInterest)}/mo`}
          detail={`${termYears}-year fully amortizing payment`}
        />
        <ResultCard
          label="Taxes & insurance"
          value={`${currency(
            result.monthlyTax + result.monthlyInsurance
          )}/mo`}
          detail={`${currency(result.monthlyTax)} taxes · ${currency(
            result.monthlyInsurance
          )} insurance`}
        />
        <ResultCard
          label="Mortgage insurance & HOA"
          value={`${currency(
            result.monthlyMortgageInsurance + monthlyHoa
          )}/mo`}
          detail={`${currency(
            result.monthlyMortgageInsurance
          )} mortgage insurance · ${currency(monthlyHoa)} HOA`}
        />
        <ResultCard
          label="Total housing payment"
          value={`${currency(result.totalHousingPayment)}/mo`}
          detail="Principal, interest, taxes, insurance, mortgage insurance, and HOA"
          accent="#a5f3fc"
        />
        <ResultCard
          label="Housing ratio"
          value={`${result.housingDti.toFixed(1)}%`}
          detail="Total housing payment ÷ gross monthly income"
        />
        <ResultCard
          label="Total DTI"
          value={`${result.totalDti.toFixed(1)}%`}
          detail="Housing payment plus existing monthly debts ÷ gross monthly income"
          accent={result.withinTarget ? "#86efac" : "#fca5a5"}
        />
        <ResultCard
          label={`Housing allowance at ${targetDti.toFixed(1)}% DTI`}
          value={`${currency(result.maximumHousingPayment)}/mo`}
          detail="Maximum total debt allowance minus existing monthly debts"
        />
        <ResultCard
          label="Estimated maximum price"
          value={currency(result.maximumPurchasePrice)}
          detail="Uses the same rate, term, down payment, taxes, insurance, HOA, fees, and DTI target"
        />
        <ResultCard
          label="Estimated cash to close"
          value={currency(result.estimatedCashToClose)}
          detail="Down payment plus entered closing-cost percentage; excludes credits, prepaids, and reserves"
        />
      </div>

      <div
        style={{
          marginTop: 18,
          borderRadius: 18,
          padding: 16,
          border: result.withinTarget
            ? "1px solid rgba(34,197,94,0.28)"
            : "1px solid rgba(239,68,68,0.30)",
          background: result.withinTarget
            ? "rgba(22,101,52,0.18)"
            : "rgba(127,29,29,0.18)",
          color: result.withinTarget ? "#bbf7d0" : "#fecaca",
          fontSize: 14,
          fontWeight: 800,
          lineHeight: 1.55,
        }}
      >
        {result.withinTarget
          ? `This scenario is within the selected ${targetDti.toFixed(
              1
            )}% total-DTI target.`
          : `This scenario exceeds the selected ${targetDti.toFixed(
              1
            )}% total-DTI target.`}
      </div>

      <div
        style={{
          marginTop: 18,
          borderRadius: 22,
          padding: 20,
          border: "1px solid rgba(34,211,238,0.28)",
          background:
            "linear-gradient(135deg, rgba(8,145,178,0.16), rgba(15,23,42,0.42))",
        }}
      >
        <div
          style={{
            color: "rgba(255,255,255,0.58)",
            fontSize: 11,
            fontWeight: 900,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}
        >
          Estimated affordability range
        </div>
        <div
          style={{
            marginTop: 8,
            color: "#a5f3fc",
            fontSize: 30,
            fontWeight: 950,
            letterSpacing: "-0.04em",
          }}
        >
          {currency(result.conservativePurchasePrice)} –{" "}
          {currency(result.maximumPurchasePrice)}
        </div>
        <div
          style={{
            marginTop: 9,
            color: "rgba(255,255,255,0.62)",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          The lower end uses a more conservative{" "}
          {result.conservativeDti.toFixed(1)}% total-DTI limit. The upper end
          uses your selected {targetDti.toFixed(1)}% limit. Both use the
          entered gross income, monthly debts, {downPaymentPercent.toFixed(1)}%
          down payment, interest rate, term, taxes, insurance, mortgage
          insurance, financed fee, and HOA.
        </div>
      </div>

      <div
        style={{
          marginTop: 14,
          color: "rgba(255,255,255,0.46)",
          fontSize: 12,
          lineHeight: 1.65,
        }}
      >
        Educational estimate only—not a prequalification, approval, or
        commitment to lend. Actual underwriting verifies income, assets,
        employment, debts, credit, reserves, occupancy, property eligibility,
        loan limits, and automated underwriting findings. DTI limits, mortgage
        insurance, funding or guarantee fees, taxes, insurance, and closing
        costs vary by borrower, lender, property, and loan program.
      </div>
    </section>
  );
}
