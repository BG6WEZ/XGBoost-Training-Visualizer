/**
 * 参数校验工具
 * 
 * 提供前端参数校验，与后端规则保持一致
 */

export enum ValidationRuleCode {
  LOW_LR_LOW_ESTIMATORS = 'LOW_LR_LOW_ESTIMATORS',
  HIGH_DEPTH_HIGH_SAMPLE = 'HIGH_DEPTH_HIGH_SAMPLE',
  EARLY_STOPPING_TOO_LARGE = 'EARLY_STOPPING_TOO_LARGE',
  HIGH_DEPTH_LOW_CHILD_WEIGHT = 'HIGH_DEPTH_LOW_CHILD_WEIGHT',
  LEARNING_RATE_OUT_OF_RANGE = 'LEARNING_RATE_OUT_OF_RANGE',
  N_ESTIMATORS_TOO_SMALL = 'N_ESTIMATORS_TOO_SMALL',
  MAX_DEPTH_OUT_OF_RANGE = 'MAX_DEPTH_OUT_OF_RANGE',
  SUBSAMPLE_OUT_OF_RANGE = 'SUBSAMPLE_OUT_OF_RANGE',
  COLSAMPLE_OUT_OF_RANGE = 'COLSAMPLE_OUT_OF_RANGE',
  EARLY_STOPPING_INVALID = 'EARLY_STOPPING_INVALID',
}

export interface FieldError {
  fields: string[]
  rule: string
  current: Record<string, unknown>
  suggestion: string
}

export interface ValidationResult {
  valid: boolean
  fieldErrors: FieldError[]
}

export interface TrainingParams {
  learning_rate: number
  max_depth: number
  n_estimators: number
  subsample: number
  colsample_bytree: number
  early_stopping_rounds?: number | null
  min_child_weight?: number
}

export function validateTrainingParams(params: TrainingParams): ValidationResult {
  const fieldErrors: FieldError[] = []

  if (params.learning_rate < 0.001 || params.learning_rate > 1.0) {
    fieldErrors.push({
      fields: ['learning_rate'],
      rule: ValidationRuleCode.LEARNING_RATE_OUT_OF_RANGE,
      current: { learning_rate: params.learning_rate },
      suggestion: '学习率应在 0.001 到 1.0 之间',
    })
  }

  if (params.n_estimators < 10) {
    fieldErrors.push({
      fields: ['n_estimators'],
      rule: ValidationRuleCode.N_ESTIMATORS_TOO_SMALL,
      current: { n_estimators: params.n_estimators },
      suggestion: 'n_estimators 应至少为 10',
    })
  }

  if (params.max_depth < 1 || params.max_depth > 15) {
    fieldErrors.push({
      fields: ['max_depth'],
      rule: ValidationRuleCode.MAX_DEPTH_OUT_OF_RANGE,
      current: { max_depth: params.max_depth },
      suggestion: 'max_depth 应在 1 到 15 之间',
    })
  }

  if (params.subsample < 0.1 || params.subsample > 1.0) {
    fieldErrors.push({
      fields: ['subsample'],
      rule: ValidationRuleCode.SUBSAMPLE_OUT_OF_RANGE,
      current: { subsample: params.subsample },
      suggestion: 'subsample 应在 0.1 到 1.0 之间',
    })
  }

  if (params.colsample_bytree < 0.1 || params.colsample_bytree > 1.0) {
    fieldErrors.push({
      fields: ['colsample_bytree'],
      rule: ValidationRuleCode.COLSAMPLE_OUT_OF_RANGE,
      current: { colsample_bytree: params.colsample_bytree },
      suggestion: 'colsample_bytree 应在 0.1 到 1.0 之间',
    })
  }

  if (params.early_stopping_rounds !== null && params.early_stopping_rounds !== undefined) {
    if (params.early_stopping_rounds < 1) {
      fieldErrors.push({
        fields: ['early_stopping_rounds'],
        rule: ValidationRuleCode.EARLY_STOPPING_INVALID,
        current: { early_stopping_rounds: params.early_stopping_rounds },
        suggestion: 'early_stopping_rounds 应至少为 1',
      })
    } else if (params.early_stopping_rounds >= params.n_estimators) {
      fieldErrors.push({
        fields: ['early_stopping_rounds', 'n_estimators'],
        rule: ValidationRuleCode.EARLY_STOPPING_TOO_LARGE,
        current: {
          early_stopping_rounds: params.early_stopping_rounds,
          n_estimators: params.n_estimators,
        },
        suggestion: 'early_stopping_rounds 应小于 n_estimators',
      })
    }
  }

  if (params.learning_rate <= 0.02 && params.n_estimators < 150) {
    fieldErrors.push({
      fields: ['learning_rate', 'n_estimators'],
      rule: ValidationRuleCode.LOW_LR_LOW_ESTIMATORS,
      current: {
        learning_rate: params.learning_rate,
        n_estimators: params.n_estimators,
      },
      suggestion: '低学习率配合低迭代轮数可能导致欠拟合。建议将 n_estimators 提高到 >=150，或将 learning_rate 提升到 >=0.05',
    })
  }

  if (params.max_depth >= 10 && params.subsample >= 0.95 && params.colsample_bytree >= 0.95) {
    fieldErrors.push({
      fields: ['max_depth', 'subsample', 'colsample_bytree'],
      rule: ValidationRuleCode.HIGH_DEPTH_HIGH_SAMPLE,
      current: {
        max_depth: params.max_depth,
        subsample: params.subsample,
        colsample_bytree: params.colsample_bytree,
      },
      suggestion: '高深度配合高采样率可能导致过拟合。建议降低 max_depth 到 <10，或降低 subsample/colsample_bytree 到 <0.95',
    })
  }

  const minChildWeight = params.min_child_weight ?? 1.0
  if (params.max_depth >= 10 && minChildWeight < 1.0) {
    fieldErrors.push({
      fields: ['max_depth', 'min_child_weight'],
      rule: ValidationRuleCode.HIGH_DEPTH_LOW_CHILD_WEIGHT,
      current: {
        max_depth: params.max_depth,
        min_child_weight: minChildWeight,
      },
      suggestion: '高深度时 min_child_weight 过低可能导致过拟合。建议将 min_child_weight 提高到 >=1.0，或降低 max_depth',
    })
  }

  return {
    valid: fieldErrors.length === 0,
    fieldErrors,
  }
}

export function formatValidationErrors(errors: FieldError[]): string {
  return errors.map((e) => `• ${e.suggestion}`).join('\n')
}
