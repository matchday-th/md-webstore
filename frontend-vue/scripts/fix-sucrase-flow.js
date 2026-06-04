import fs from 'fs';
import path from 'path';

const pluginPath = path.resolve('node_modules/sucrase/dist/parser/plugins/flow.js');
const pluginDir = path.dirname(pluginPath);

if (!fs.existsSync(pluginPath)) {
  fs.mkdirSync(pluginDir, { recursive: true });
  fs.writeFileSync(
    pluginPath,
    '"use strict";Object.defineProperty(exports, "__esModule", {value: true});\n' +
      'const noop = () => {};\nconst falseFn = () => false;\n' +
      'exports.flowParseMaybeAssign = noop;\n' +
      'exports.flowParseSubscripts = noop;\n' +
      'exports.flowParseSubscript = noop;\n' +
      'exports.flowStartParseAsyncArrowFromCallExpression = noop;\n' +
      'exports.flowParseArrow = noop;\n' +
      'exports.flowStartParseNewArguments = noop;\n' +
      'exports.flowStartParseObjPropValue = noop;\n' +
      'exports.flowParseVariance = noop;\n' +
      'exports.flowParseFunctionBodyAndFinish = noop;\n' +
      'exports.flowTryParseStatement = falseFn;\n' +
      'exports.flowParseIdentifierStatement = noop;\n' +
      'exports.flowAfterParseVarHead = noop;\n' +
      'exports.flowStartParseFunctionParams = noop;\n' +
      'exports.flowParseTypeParameterDeclaration = noop;\n' +
      'exports.flowParseTypeAnnotation = noop;\n' +
      'exports.flowAfterParseClassSuper = noop;\n' +
      'exports.flowTryParseExportDefaultExpression = falseFn;\n' +
      'exports.flowParseExportDeclaration = noop;\n' +
      'exports.flowShouldDisallowExportDefaultSpecifier = falseFn;\n' +
      'exports.flowShouldParseExportStar = falseFn;\n' +
      'exports.flowParseExportStar = noop;\n' +
      'exports.flowShouldParseExportDeclaration = falseFn;\n' +
      'exports.flowStartParseImportSpecifiers = noop;\n' +
      'exports.flowParseImportSpecifier = noop;\n' +
      'exports.flowParseAssignableListItemTypes = noop;\n'
  );
}
